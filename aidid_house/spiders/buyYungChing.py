import re
import json
import scrapy
from aidid_house.items import AididHouseItem


class BuyyongchingSpider(scrapy.Spider):
    name = "buyYungChing"
    allowed_domains = ["buy.yungching.com.tw"]
    areas = [
        "台北市", "新北市", "桃園市", "台中市", "台南市", "高雄市", "基隆市", "新竹市", "嘉義市", "宜蘭縣",
        "新竹縣", "苗栗縣", "彰化縣", "南投縣", "雲林縣", "嘉義縣", "屏東縣", "花蓮縣", "台東縣",
        "澎湖縣", "金門縣", "連江縣"
    ]
    start_urls = [f"https://buy.yungching.com.tw/list/{city}-_c" for city in areas]

    def parse(self, response):
        raw = response.xpath('//script[@id="ng-state"]/text()').get()
        if not raw:
            self.logger.error("No <script id='ng-state'> found!")
            return

        data = json.loads(raw)

        def find_total_page_count(obj):
            if isinstance(obj, dict):
                if "totalPageCount" in obj:
                    return obj["totalPageCount"]
                for v in obj.values():
                    res = find_total_page_count(v)
                    if res is not None:
                        return res
            elif isinstance(obj, list):
                for item in obj:
                    res = find_total_page_count(item)
                    if res is not None:
                        return res
            return None

        total_pages = find_total_page_count(data) or 1
        for i in range(1, total_pages + 1):
            yield scrapy.Request(
                f"{response.url}/?pg={i}",
                callback=self.parse_list_page,
                meta={"proxy": "https://derek5g:s2Ep_52qpMyjM6iNlv@dc.decodo.com:10000"}
            )

    def parse_list_page(self, response):
        urls = response.xpath('//yc-ng-buy-house-card/a/@href').getall()
        for url in urls:
            full_url = response.urljoin(url)
            yield scrapy.Request(
                full_url,
                callback=self.parse_case_page,
                meta={"proxy": "https://derek5g:s2Ep_52qpMyjM6iNlv@dc.decodo.com:10000"}
            )

    def parse_case_page(self, response):
        try:
            raw = response.xpath('//script[@id="ng-state"]/text()').get()
            if not raw:
                self.logger.error(f"No case JSON found at {response.url}")
                return

            data = json.loads(raw)
            case_data = next(iter(data.values()))['b']['data']

            # Basic fields
            item = AididHouseItem(
                url=response.url,
                site='永慶房屋',
                name=case_data.get("caseName"),
                address=case_data.get("address"),
                city=case_data.get("county"),
                district=case_data.get("district"),
                latitude=case_data.get("geoInfo", {}).get("latitude"),
                longitude=case_data.get("geoInfo", {}).get("longitude"),
                price=case_data.get("price"),
                layout=response.xpath('//div[contains(@class, "room")]/text()').get(),
                age=response.xpath('//div[contains(@class, "age")]/text()').re_first(r'屋齡([\d.]+)\s*年'),
                space=' '.join(response.xpath('//div[contains(@class, "regarea")]//text()').getall()).strip(),
                floors=response.xpath('//div[contains(@class, "floor")]/text()').get(),
                community=response.xpath('//a[contains(@class, "community gtmPushEvent")]/h3/text()').get(),
                basic_info=case_data,
                features=case_data.get("caseFeature"),
                life_info=[],
                utility_info=[],
                review='',
                images=[f"https:{img.split(',')[0].split()[0].strip()}" for img in response.xpath('//div[@block_name="buy_buydetail_photos"]//img/@srcset').getall() if img]
            )

            # Prepare POI API request
            house_id = response.url.split('/')[-1]
            poi_api_url = f"https://buy.yungching.com.tw/api/v2/information/poi?id={house_id}"
            headers = {
                "referer": response.url,
                "sec-fetch-dest": "empty",
                "sec-fetch-mode": "cors",
                "sec-fetch-site": "same-origin",
                "priority": "u=1, i",
            }
            yield scrapy.Request(
                poi_api_url,
                callback=self.parse_poi_data,
                headers=headers,
                meta={"item": item, "proxy": "https://derek5g:s2Ep_52qpMyjM6iNlv@dc.decodo.com:10000"}
            )

        except Exception as e:
            self.logger.error(f"Error parsing case page {response.url}: {e}")

    def parse_poi_data(self, response):
        item = response.meta["item"]
        try:
            pois = json.loads(response.text).get("data", {}).get("pois", [])
            life_categories = {"休閒娛樂", "超商", "停車場", "購物"}
            utility_categories = {"交通", "醫療", "政府", "學校"}

            life_list, util_list = [], []
            for poi in pois:
                cat = poi.get("poiItem")
                for detail in poi.get("poiDetails", []):
                    entry = {
                        "poiSubName": detail.get("poiSubName"),
                        "poiTitle": detail.get("poiTitle"),
                        "poiLat": detail.get("poiLat"),
                        "poiLng": detail.get("poiLng"),
                        "distance": detail.get("distance"),
                        "walkTime": detail.get("walkTime"),
                        "walkDistance": detail.get("walkDistance")
                    }
                    if cat in life_categories:
                        life_list.append(entry)
                    elif cat in utility_categories:
                        util_list.append(entry)

            item["life_info"] = life_list
            item["utility_info"] = util_list
        except Exception as e:
            self.logger.error(f"Error parsing POI data: {e}")

        # Finally, yield the enriched item
        yield item
