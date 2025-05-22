import scrapy
import json
import re
from urllib.parse import quote
from urllib.parse import urljoin
from aidid_house.items import SalesmanItem


class Salesman5168Spider(scrapy.Spider):
    name = "5168_salesman"
    allowed_domains = ["buy.houseprice.tw", "realtor.houseprice.tw"]
    proxy = "https://dereksun:WrVt~x79Y0jGugas1r@gate.decodo.com:7000"

    areas = [
        "台北市", "新北市", "桃園市", "台中市", "台南市", "高雄市", "基隆市", "新竹市", "嘉義市", "宜蘭縣",
        "新竹縣", "苗栗縣", "彰化縣", "南投縣", "雲林縣", "嘉義縣", "屏東縣", "花蓮縣", "台東縣",
        "澎湖縣", "金門縣", "連江縣"
    ]


    def start_requests(self):
        """Generate API requests for each city."""
        for city in self.areas:
            city_encoded = quote(city)  # URL encode the city name
            api_url = f"https://buy.houseprice.tw/ws/BuyCaseList/Search/{city_encoded}_city/"
            yield scrapy.Request(
                url=api_url,
                callback=self.parse_api,
                meta={"city": city, "proxy": "https://dereksun:WrVt~x79Y0jGugas1r@gate.decodo.com:7000"}
            )

    def parse_api(self, response):
        """Parse the API response to get total page count and initiate requests for each page."""
        try:
            api_data = json.loads(response.text)
            total_page_count = api_data.get("page", {}).get("totalPageCount", 0)
            city = response.meta["city"]
            for page in range(1, total_page_count + 1):
                page_url = f"https://buy.houseprice.tw/list/{quote(city)}_city/?p={page}"
                yield scrapy.Request(
                    url=page_url,
                    callback=self.parse_page_for_ids,
                    meta={"city": city, "page": page, "proxy": "https://dereksun:WrVt~x79Y0jGugas1r@gate.decodo.com:7000"}
                )
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse API response for city {response.meta['city']}: {e}")

    def parse_page_for_ids(self, response):
        case_links = response.xpath('//a[contains(@href, "/house/")]/@href').getall()
        for case_link in case_links:
            match = re.search(r'/house/(\d+)', case_link)
            if match:
                case_id = match.group(1)
                property_actual_url = response.urljoin(case_link)
                api_url = f"https://buy.houseprice.tw/ws/BuyCaseDetail/{case_id}"
                yield scrapy.Request(
                    url=api_url,
                    callback=self.parse_salesman_api,
                    meta={"proxy": "https://dereksun:WrVt~x79Y0jGugas1r@gate.decodo.com:7000", "property_url": property_actual_url}
                )

    def parse_salesman_api(self, response):
        try:
            data = json.loads(response.text)
            owner_info = data.get("caseOwnerInfo")
            property_url_from_meta = response.meta.get("property_url", response.url)

            if owner_info:
                item = SalesmanItem()
                item['site'] = "5168"
                item['salesman'] = owner_info.get("name")

                phone_raw = owner_info.get("phone")
                item['phone'] = phone_raw.replace('-', '').replace(' ', '') if phone_raw else None

                if item['phone']:
                    item['link'] = f"https://realtor.houseprice.tw/agent/buy/{item['phone']}/"
                else:
                    item['link'] = None

                item['brand_name'] = owner_info.get("brand")
                item['store_name'] = owner_info.get("contactStore")
                item['legal_company_name'] = owner_info.get("contactCompany")
                item['profile_image_url'] = owner_info.get("profilePicture")  # Get profile image

                item['property_url'] = property_url_from_meta

                yield item
            else:
                self.logger.warning(f"No caseOwnerInfo found in API response for {response.url}")

        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse JSON from Salesman API {response.url}: {e}")
        except Exception as e:
            self.logger.error(f"Unexpected error in parse_salesman_api for {response.url}: {e}")