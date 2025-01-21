import scrapy
from aidid_house.items import AididHouseItem
import re
import json


class BuyrakuyaSpider(scrapy.Spider):
    name = "buyRakuya"
    allowed_domains = ["www.rakuya.com.tw"]
    start_urls = [f"https://www.rakuya.com.tw/sell/result?city={i}" for i in range(1, 21)]

    def parse(self, response):
        # Extract the content of the <script> tag
        script_content = response.css('script::text').re_first(r'window\.sellSearch\s*=\s*(\{.*?\});')
        if script_content:
            try:
                sell_search_data = json.loads(script_content)
                page_count = sell_search_data.get('pagination', {}).get('pageCount', 0)
                if page_count:
                    for page in range(1, page_count + 1):
                        url = f"{response.url}&page={page}"
                        yield scrapy.Request(url=url, callback=self.parse_pages, meta={"proxy": "https://dc.smartproxy.com:10000"})
            except json.JSONDecodeError as e:
                self.logger.error(f"Error parsing JSON: {e}")

    def parse_pages(self, response):
        cases = response.xpath('//div[@class="box__communityIntro"]/section/a/@href').getall()
        for case in cases:
            yield scrapy.Request(url=response.urljoin(case), callback=self.parse_case, meta={"proxy": "https://dc.smartproxy.com:10000"})

    def parse_case(self, response):
        site = "樂屋網"
        url = response.url
        data_str = response.css('script::text').re_first(r'window\.tmpDataLayer\s*=\s*(\{.*?\});')
        data = json.loads(data_str)
        item_data = data.get("itemData", {})

        # Extract layout information
        layout_match = re.search(r'格局為([\u4e00-\u9fa5\d]+)', response.text)
        layout = layout_match.group(1) if layout_match else ""

        # Extract required fields
        name = item_data.get("item_name", "")
        house_id = item_data.get("item_id", "")
        price = item_data.get("price", 0)
        age = item_data.get("age", 0.0)
        space = item_data.get("item_variant", 0.0)
        object_tag = item_data.get("object_tag", "")
        floor = item_data.get("object_floor", 0)

        # Extract address and community
        json_data_match = re.search(r'<script type="application/ld\+json">(.+?)</script>', response.text, re.DOTALL)
        if json_data_match:
            json_data_str = json_data_match.group(1)
            data = json.loads(json_data_str)
            address_data = data.get("address", {})
            city = address_data.get("addressLocality", "")
            district = address_data.get("addressRegion", "")
            street_address = address_data.get("streetAddress", "")
            full_address = f"{city}{district}{street_address}"
            image_url = response.css('meta[property="og:image"]::attr(content)').get()
            images = [image_url]

        # Extract community name
        community_tag = response.css('a[href*="/community/"]')
        community_url = community_tag.attrib.get("href", "")
        community = community_tag.css("::text").get().strip() if community_tag else ""

        # Make API request for additional info
        if house_id:
            api_url = f"https://www.rakuya.com.tw/sell_item/api/item-environment/list?ehid={house_id}"
            yield scrapy.Request(url=api_url, callback=self.parse_api_response, meta={
                "url": url,
                "house_id": house_id,
                "site": site,
                "name": name,
                "address": full_address,
                "city": city,
                "district": district,
                "price": price,
                "layout": layout,
                "age": age,
                "space": space,
                "floors": floor,
                "community": community,
                "basic_info": {},
                "features": object_tag,
                "review": '',
                "images": images,
                "trade_data": {},
                "proxy": "https://dc.smartproxy.com:10000"
            })

    def parse_api_response(self, response):
        try:
            api_data = json.loads(response.text)
            if api_data.get("status"):
                data = api_data.get("data", {})
                latitude = data.get("itemLat", "")
                longitude = data.get("itemLng", "")

                # Extract utility and life information
                utility_info = {
                    "medical": data.get("medical", {}).get("poiList", []),
                    "transport": data.get("transport", {}).get("poiList", []),
                    "school": data.get("school", {}).get("poiList", []),
                    "avoid": data.get("avoid", {}).get("poiList", []),
                }
                life_info = {
                    "food": data.get("food", {}).get("poiList", []),
                    "market": data.get("market", {}).get("poiList", []),
                    "park": data.get("park", {}).get("poiList", []),
                }

                item = AididHouseItem(
                    url=response.meta["url"],
                    house_id=response.meta["house_id"],
                    site=response.meta["site"],
                    name=response.meta["name"],
                    address=response.meta["address"],
                    latitude=latitude,
                    longitude=longitude,
                    city=response.meta["city"],
                    district=response.meta["district"],
                    price=response.meta["price"],
                    layout=response.meta["layout"],
                    age=response.meta["age"],
                    space=response.meta["space"],
                    floors=response.meta["floors"],
                    community=response.meta["community"],
                    basic_info=response.meta["basic_info"],
                    features=response.meta["features"],
                    life_info=life_info,
                    utility_info=utility_info,
                    review=response.meta["review"],
                    images=response.meta["images"],
                    trade_data=response.meta["trade_data"],
                )

                yield item
        except json.JSONDecodeError as e:
            self.logger.error(f"Error parsing API response: {e}")
