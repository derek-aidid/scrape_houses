import scrapy
from urllib.parse import quote
import json
import re
from aidid_house.items import AididHouseItem

class Buy5168Spider(scrapy.Spider):
    name = "buy5168"
    allowed_domains = ["buy.houseprice.tw"]

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
                meta={"city": city, "proxy": "https://dereksun:q2av~lZjj4Rq5md9SP@gate.decodo.com:7000"}
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
                    callback=self.parse_page,
                    meta={"city": city, "page": page, "proxy": "https://dereksun:q2av~lZjj4Rq5md9SP@gate.decodo.com:7000"}
                )
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse API response for city {response.meta['city']}: {e}")

    def parse_page(self, response):
        """Parse individual page data."""
        cases = response.xpath('//a[contains(@href, "/house/")]/@href').getall()
        for case in cases:
            case_url = response.urljoin(case)
            yield scrapy.Request(
                url=case_url,
                callback=self.parse_case,
                meta={"city": response.meta["city"], "page": response.meta["page"], "proxy": "https://dereksun:q2av~lZjj4Rq5md9SP@gate.decodo.com:7000"}
            )

    def parse_case(self, response):
        """Parse detailed information for each property case."""
        site = '5168'
        url = response.url

        city = response.meta.get("city", None)
        name = response.xpath('//div/h1/text()').get() or None

        address = response.xpath('//div[@class="text-[18px]"]/text()').get()
        address = address.strip() if address else None

        city_district_match = re.search(r'(\w+(?:市|縣))(\w+(?:區|鄉|鎮|市|鄉))', address) if address else None
        district = city_district_match.group(2) if city_district_match else None

        price = response.xpath(
            '//div[@class="w-[145px] shrink-0"]/span[contains(@class, "font-bold")]/text()'
        ).get()
        price = price.strip().replace(',', '') if price else None

        space = response.xpath('//li[div[contains(text(), "建坪")]]/div[2]/text()').get()
        space = space.strip() if space else None

        floors = response.xpath('//li[div[contains(text(), "樓層")]]/div[2]/text()').get()
        floors = floors.strip() if floors else None

        layout = response.xpath('//li[div[contains(text(), "格局")]]/div[2]/text()').get()
        layout = layout.strip() if layout else None

        age = response.xpath('//li[div[contains(text(), "屋齡")]]/div[2]/text()').get()
        age = age.strip() if age else None

        lat_lon = response.xpath('//a[contains(@href, "maps/search")]/@href').re_first(r'query=([\d.]+,[\d.]+)')
        latitude, longitude = lat_lon.split(",") if lat_lon else (None, None)

        community_name = response.xpath('//span[contains(text(), "社區")]/following-sibling::a/text()').get()
        community_name = community_name.strip() if community_name else None

        image_urls = response.xpath('//div[@class="house_images"]//img/@src').getall() or []

        feature_description = response.xpath(
            '//div[@class="line-clamp-6 mb-7 text-lg whitespace-pre-line"]/text()'
        ).getall()
        features = ''.join(feature_description).strip() if feature_description else None

        basic_info_dict = {}
        basic_infos = response.xpath('//div[@class="grid grid-cols-3 gap-2 text-lg"]/div')
        for basic_info in basic_infos:
            raw_html = basic_info.get()
            title = basic_info.xpath('./span/text()').get()
            value = raw_html.split('</span>')[-1].strip() if '</span>' in raw_html else None
            if title and value:
                clean_value = value.replace("\n", "").replace("</div>", "").strip()
                basic_info_dict[title.strip()] = clean_value

        area_infos = response.xpath('//div[@class="grid grid-cols-3 gap-2 text-lg p-4 bg-gray-100 mb-2"]/div')
        for area_info in area_infos:
            raw_html = area_info.get()
            title = area_info.xpath('./span/text()').get()
            value = raw_html.split('</span>')[-1].strip() if '</span>' in raw_html else None
            if title and value:
                clean_value = value.replace("\n", "").replace("</div>", "").strip()
                basic_info_dict[title.strip()] = clean_value

        extra_infos = response.xpath('//div[@class="text-lg"]')
        for extra_info in extra_infos:
            raw_html = extra_info.get()
            title = extra_info.xpath('./span/text()').get()
            value = raw_html.split('</span>')[-1].strip() if '</span>' in raw_html else None
            if title and value:
                clean_value = value.replace("\n", "").replace("</div>", "").strip()
                basic_info_dict[title.strip()] = clean_value

        # Yield the item directly since house_id-related API call has been removed.
        item = AididHouseItem(
            url=url,
            site=site,
            name=name,
            address=address,
            latitude=latitude,
            longitude=longitude,
            city=city,
            district=district,
            price=price,
            layout=layout,
            age=age,
            space=space,
            floors=floors,
            community=community_name,
            basic_info=basic_info_dict,  # JSON field
            features=features,
            life_info=[],         # Set as empty list (modify as needed)
            utility_info=[],      # Set as empty list (modify as needed)
            review='',
            images=image_urls,
            trade_data=[]         # Set as empty list (modify as needed)
        )

        yield item
