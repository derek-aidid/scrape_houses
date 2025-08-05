import scrapy
import re
import json
from urllib.parse import urlparse, parse_qs
from aidid_house.items import AididHouseItem, HouseUpdateItem

class BuyrakuyaSpider(scrapy.Spider):
    name = "buyRakuya"
    allowed_domains = ["www.rakuya.com.tw"]
    
    # This will be populated by the pipeline
    existing_urls = set()
    
    start_urls = [f"https://www.rakuya.com.tw/sell/result?city={i}" for i in range(1, 21)]

    def parse(self, response):
        script_content = response.css('script::text').re_first(r'window\.sellSearch\s*=\s*(\{.*?\});')
        if not script_content:
            return
        try:
            sell_search_data = json.loads(script_content)
            page_count = sell_search_data.get('pagination', {}).get('pageCount', 0)
            for page in range(1, page_count + 1):
                yield scrapy.Request(
                    url=f"{response.url}&page={page}",
                    callback=self.parse_pages,
                    meta={"proxy": "https://dereksun:L4m2_7cFdsl0GAaepi@gate.decodo.com:7000"}
                )
        except json.JSONDecodeError as e:
            self.logger.error(f"Error parsing JSON: {e}")

    def parse_pages(self, response):
        for href in response.xpath('//div[@class="box__communityIntro"]/section/a/@href').getall():
            full_url = response.urljoin(href)
            
            if full_url in self.existing_urls:
                # It's an existing house, just send an update signal
                yield HouseUpdateItem(url=full_url)
            else:
                # It's a new house, scrape the full details
                yield scrapy.Request(
                    url=full_url,
                    callback=self.parse_case,
                    meta={"proxy": "https://dereksun:L4m2_7cFdsl0GAaepi@gate.decodo.com:7000"}
                )

    def parse_case(self, response):
        site = "樂屋網"
        url = response.url

        # --- parse the inline JS dataLayer for itemData ---
        data_str = response.css('script::text') \
                           .re_first(r'window\.tmpDataLayer\s*=\s*(\{.*?\});')
        data = json.loads(data_str or "{}")
        item_data = data.get("itemData", {})

        # --- your existing field extractions ---
        name      = item_data.get("item_name", "")
        price     = item_data.get("price", 0)
        age       = item_data.get("age", 0.0)
        raw_space = item_data.get("item_variant", 0.0)
        space = f"{raw_space}坪"
        object_tag= item_data.get("object_tag", "")
        floor     = item_data.get("object_floor", 0)

        layout_match = re.search(r'格局為([\u4e00-\u9fa5\d]+)', response.text)
        layout = layout_match.group(1) if layout_match else ""

        # --- ld+json for address & images ---
        ld_json = re.search(r'<script type="application/ld\+json">(.+?)</script>',
                             response.text, re.DOTALL)
        if ld_json:
            ld = json.loads(ld_json.group(1))
            addr = ld.get("address", {})
            city    = addr.get("addressLocality", "")
            district= addr.get("addressRegion", "")
            street  = addr.get("streetAddress", "")
            full_address = f"{city}{district}{street}"
            img = response.css('meta[property="og:image"]::attr(content)').get()
            images = [img] if img else []
        else:
            city = district = full_address = ""
            images = []

        community_tag = response.css('a[href*="/community/"]')
        community = community_tag.css("::text").get(default="").strip()

        # --- extract house_id (ehid) from URL query ---
        parsed = urlparse(url)
        qs = parse_qs(parsed.query)
        ehid_list = qs.get("ehid", [])
        house_id = ehid_list[0] if ehid_list else None

        # if we have an ehid, go call the environment API
        if house_id:
            api_url = (
                "https://www.rakuya.com.tw/"
                f"sell_item/api/item-environment/list?ehid={house_id}"
            )
            # pack everything we already have into meta
            meta = {
                "item_fields": {
                    "url":        url,
                    "house_id":   house_id,
                    "site":       site,
                    "name":       name,
                    "address":    full_address,
                    "city":       city,
                    "district":   district,
                    "price":      price,
                    "layout":     layout,
                    "age":        age,
                    "space":      space,
                    "floors":     floor,
                    "community":  community,
                    "basic_info": {},
                    "features":   object_tag,
                    "review":     "",
                    "images":     images,
                    "trade_data": {}
                },
                "proxy": "https://dereksun:L4m2_7cFdsl0GAaepi@gate.decodo.com:7000"
            }
            yield scrapy.Request(
                url=api_url,
                callback=self.parse_api_response,
                meta=meta
            )
        else:
            # fallback: no house_id → yield what we have
            yield AididHouseItem(
                url=url, site=site, name=name, address=full_address,
                latitude="", longitude="", city=city, district=district,
                price=price, layout=layout, age=age, space=space,
                floors=floor, community=community, basic_info={},
                features=object_tag, life_info={}, utility_info={},
                review="", images=images, trade_data={}, house_id=""
            )

    def parse_api_response(self, response):
        fields = response.meta["item_fields"]
        try:
            api = json.loads(response.text)
            data = api.get("data", {})

            # geo
            fields["latitude"]  = data.get("itemLat", "")
            fields["longitude"] = data.get("itemLng", "")

            # utility vs life
            fields["utility_info"] = {
                "medical":   data.get("medical", {}).get("poiList", []),
                "transport": data.get("transport", {}).get("poiList", []),
                "school":    data.get("school", {}).get("poiList", []),
                "avoid":     data.get("avoid", {}).get("poiList", []),
            }
            fields["life_info"] = {
                "food":   data.get("food", {}).get("poiList", []),
                "market": data.get("market", {}).get("poiList", []),
                "park":   data.get("park", {}).get("poiList", []),
            }
        except Exception as e:
            self.logger.error(f"Error parsing API response for {fields['house_id']}: {e}")
            fields["latitude"] = fields["longitude"] = ""
            fields["utility_info"] = fields["life_info"] = {}

        # build and yield final item
        yield AididHouseItem(**fields)
