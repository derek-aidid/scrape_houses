import scrapy
from aidid_house.items import AididHouseItem
import re
import json

class BuyrakuyaSpider(scrapy.Spider):
    name = "buyRakuya"
    allowed_domains = ["www.rakuya.com.tw"]
    start_urls = [f"https://www.rakuya.com.tw/sell/result?city={i}" for i in range(1, 21)]

    def parse(self, response):
        # Extract the content of the <script> tag containing sellSearch data.
        script_content = response.css('script::text').re_first(r'window\.sellSearch\s*=\s*(\{.*?\});')
        if script_content:
            try:
                sell_search_data = json.loads(script_content)
                page_count = sell_search_data.get('pagination', {}).get('pageCount', 0)
                if page_count:
                    for page in range(1, page_count + 1):
                        url = f"{response.url}&page={page}"
                        yield scrapy.Request(
                            url=url,
                            callback=self.parse_pages,
                            meta={"proxy": "https://sph891vlhw:IpHj4_37bibQk4gzLk@dc.smartproxy.com:10000"}
                        )
            except json.JSONDecodeError as e:
                self.logger.error(f"Error parsing JSON: {e}")

    def parse_pages(self, response):
        cases = response.xpath('//div[@class="box__communityIntro"]/section/a/@href').getall()
        for case in cases:
            yield scrapy.Request(
                url=response.urljoin(case),
                callback=self.parse_case,
                meta={"proxy": "https://sph891vlhw:IpHj4_37bibQk4gzLk@dc.smartproxy.com:10000"}
            )

    def parse_case(self, response):
        site = "樂屋網"
        url = response.url
        # Parse the JSON data layer
        data_str = response.css('script::text').re_first(r'window\.tmpDataLayer\s*=\s*(\{.*?\});')
        data = json.loads(data_str)
        item_data = data.get("itemData", {})

        # Extract layout information
        layout_match = re.search(r'格局為([\u4e00-\u9fa5\d]+)', response.text)
        layout = layout_match.group(1) if layout_match else ""

        # Extract required fields (house_id extraction removed)
        name = item_data.get("item_name", "")
        price = item_data.get("price", 0)
        age = item_data.get("age", 0.0)
        space = item_data.get("item_variant", 0.0)
        object_tag = item_data.get("object_tag", "")
        floor = item_data.get("object_floor", 0)

        # Extract address and community via ld+json script
        json_data_match = re.search(r'<script type="application/ld\+json">(.+?)</script>', response.text, re.DOTALL)
        if json_data_match:
            json_data_str = json_data_match.group(1)
            ld_data = json.loads(json_data_str)
            address_data = ld_data.get("address", {})
            city = address_data.get("addressLocality", "")
            district = address_data.get("addressRegion", "")
            street_address = address_data.get("streetAddress", "")
            full_address = f"{city}{district}{street_address}"
            image_url = response.css('meta[property="og:image"]::attr(content)').get()
            images = [image_url] if image_url else []
        else:
            full_address = ""
            city = ""
            district = ""
            images = []

        # Extract community name text
        community_tag = response.css('a[href*="/community/"]')
        community = community_tag.css("::text").get().strip() if community_tag else ""

        # Since we removed house_id, no API call is made; set additional fields as empty defaults.
        item = AididHouseItem(
            url=url,
            site=site,
            name=name,
            address=full_address,
            latitude="",
            longitude="",
            city=city,
            district=district,
            price=price,
            layout=layout,
            age=age,
            space=space,
            floors=floor,
            community=community,
            basic_info={},
            features=object_tag,
            life_info={},
            utility_info={},
            review='',
            images=images,
            trade_data={}
        )

        yield item
