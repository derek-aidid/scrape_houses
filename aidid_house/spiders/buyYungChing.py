import re
import json
import scrapy
from aidid_house.items import AididHouseItem

class BuyyongchingSpider(scrapy.Spider):
    name = "buyYungChing"
    allowed_domains = ["buy.yungching.com.tw"]
    # Define the areas to scrape
    areas = [
        "台北市", "新北市", "桃園市", "台中市", "台南市", "高雄市", "基隆市", "新竹市", "嘉義市", "宜蘭縣",
        "新竹縣", "苗栗縣", "彰化縣", "南投縣", "雲林縣", "嘉義縣", "屏東縣", "花蓮縣", "台東縣",
        "澎湖縣", "金門縣", "連江縣"
    ]

    def start_requests(self):
        # Use the API to fetch the total number of pages for each area
        for area in self.areas:
            api_url = f"https://buy.yungching.com.tw/api/v2/list?area={area}-&pinType=0&isAddRoom=true&pg=1&ps=30"
            yield scrapy.Request(api_url, callback=self.parse_total_pages, meta={"area": area, "proxy": "https://dc.smartproxy.com:10000"})

    def parse_total_pages(self, response):
        area = response.meta["area"]
        try:
            data = json.loads(response.text)
            total_pages = int(data["data"]["pa"]["totalPageCount"])
            if total_pages > 0:
                for page in range(1, total_pages + 1):
                    url = f"https://buy.yungching.com.tw/list/{area}-_c/?pg={page}"
                    yield scrapy.Request(url, callback=self.parse_list_page, meta={"proxy": "https://dc.smartproxy.com:10000"})
            else:
                self.logger.error(f"No pages found for area: {area}")
        except Exception as e:
            self.logger.error(f"Error parsing total pages for area {area}: {e}")

    def parse_list_page(self, response):
        # Extract property URLs from the list page
        urls = response.xpath('//yc-ng-buy-house-card/a/@href').getall()
        for url in urls:
            full_url = f'https://{url}'
            yield scrapy.Request(full_url, callback=self.parse_case_page, meta={"proxy": "https://dc.smartproxy.com:10000"})

    def parse_case_page(self, response):
        # Extract the JSON string inside the <script> tag
        json_data = response.xpath('//script[@id="ng-state"]/text()').get()

        if json_data:
            try:
                # Parse the JSON data
                data = json.loads(json_data)

                # Extract 'case_data' dynamically
                case_data = next(iter(data.values()))['b']['data']
                basic_info = case_data
                # Extract the required fields
                case_name = case_data.get("caseName")
                address = case_data.get("address")
                city = case_data.get("county")
                district = case_data.get("district")

                # Extract latitude and longitude
                geo_info = case_data.get("geoInfo", {})
                latitude = geo_info.get("latitude")
                longitude = geo_info.get("longitude")
                price = case_data.get("price")

                # Extract highlights
                highlights = case_data.get("highLights", [])
                features = " | ".join(highlights) if highlights else "無"

                build_age = response.xpath('//div[contains(@class, "age")]/text()').re_first(r'屋齡([\d.]+)\s*年')
                floors = response.xpath('//div[contains(@class, "floor")]/text()').get()
                layout = response.xpath('//div[contains(@class, "room")]/text()').get()
                # Extract all text under the div with class "regarea"
                space = response.xpath('//div[contains(@class, "regarea")]//text()').getall()
                space = ' '.join([text.strip() for text in space if text.strip()])
                community = response.xpath('//a[contains(@class, "community gtmPushEvent")]/h3/text()').get()
                images = response.xpath('//div[@block_name="buy_buydetail_photos"]//img/@srcset').getall()

                # Extract only the first URL from each srcset
                photo_urls = []
                for img_set in images:
                    first_url = img_set.split(',')[0].split()[0].strip()  # Get the first URL and strip spaces
                    if first_url:
                        full_url = f"https:{first_url}"
                        photo_urls.append(full_url)

                # Remove duplicates
                photo_urls = list(set(photo_urls))

                house_id = response.url.split('/')[-1]

                site = '永慶房屋'

                item = AididHouseItem(
                    url=response.url,
                    site=site,
                    name=case_name,
                    address=address,
                    latitude=latitude,
                    longitude=longitude,
                    city=city,
                    district=district,
                    price=price,
                    layout=layout,
                    age=build_age,
                    space=space,
                    floors=floors,
                    community=community,
                    basic_info=basic_info,
                    features=features,
                    life_info='',
                    utility_info='',
                    review='',
                    house_id=house_id,
                    images=photo_urls,
                )

                # Request POI data
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
                    meta={"item": item, "proxy": "https://dc.smartproxy.com:10000"}
                )

            except Exception as e:
                self.logger.error(f"Error parsing case page {response.url}: {e}")

    def parse_poi_data(self, response):
        # Parse POI data and update the item with life and utility info
        item = response.meta["item"]
        try:
            data = json.loads(response.text).get("data", {}).get("pois", [])

            life_categories = {"休閒娛樂", "超商", "停車場", "購物"}
            utility_categories = {"交通", "醫療", "政府", "學校"}

            life_info_list = []
            utility_info_list = []

            for poi_data in data:
                category = poi_data.get("poiItem")
                details = poi_data.get("poiDetails", [])

                for detail in details:
                    poi = {
                        "poiSubName": detail.get("poiSubName"),
                        "poiTitle": detail.get("poiTitle"),
                        "poiLat": detail.get("poiLat"),
                        "poiLng": detail.get("poiLng"),
                        "distance": detail.get("distance"),
                        "walkTime": detail.get("walkTime"),
                        "walkDistance": detail.get("walkDistance")
                    }
                    if category in life_categories:
                        life_info_list.append(poi)
                    elif category in utility_categories:
                        utility_info_list.append(poi)

            item["life_info"] = life_info_list
            item["utility_info"] = utility_info_list
        except Exception as e:
            self.logger.error(f"Error parsing POI data: {e}")
            item["life_info"] = []
            item["utility_info"] = []

        yield item