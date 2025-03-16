import scrapy
from aidid_house.items import AididHouseItem
import re
import json

class BuyxinyiSpider(scrapy.Spider):
    name = "buyXinyi"
    allowed_domains = ["www.sinyi.com.tw"]

    # Start URLs for fetching total pages dynamically
    cities = [
        "Taipei-city", "NewTaipei-city", "Keelung-city", "Yilan-county", "Hsinchu-city", "Hsinchu-county",
        "Taoyuan-city", "Miaoli-county", "Taichung-city", "Changhua-county", "Nantou-county", "Yunlin-county",
        "Chiayi-city", "Chiayi-county", "Tainan-city", "Kaohsiung-city", "Pingtung-county", "Penghu-county",
        "Taitung-county", "Hualien-county", "Kinmen-county"
    ]
    start_urls = [f"https://www.sinyi.com.tw/buy/list/{city}/default-desc/1" for city in cities]

    def parse(self, response):
        city = response.url.split('/')[-3]  # Extract the city name from URL
        # Extract total number of items from "全部 (7213)"
        total_items = response.xpath('//div[contains(text(), "全部")]/text()').re_first(r'\((\d+)\)')
        if total_items:
            total_items = int(total_items)
            items_per_page = 20  # Assuming 20 items per page
            total_pages = (total_items // items_per_page) + (1 if total_items % items_per_page else 0)

            # Generate URLs dynamically based on the total pages
            for i in range(1, total_pages + 1):
                yield scrapy.Request(
                    f"https://www.sinyi.com.tw/buy/list/{city}/default-desc/{i}", callback=self.parse_list_page
                )

    def parse_list_page(self, response):
        urls = response.xpath('//div[contains(@class, "buy-list-item")]/a/@href').getall()
        for url in urls:
            full_url = f'https://www.sinyi.com.tw{url}'
            yield scrapy.Request(full_url, callback=self.parse_case_page)

    def parse_case_page(self, response):
        # Extract the house_id from the URL
        house_id_match = re.search(r'/house/(\w+)/', response.url)
        house_id = house_id_match.group(1) if house_id_match else 'Unknown'

        name = response.xpath('//span[contains(@class, "buy-content-title-name")]/text()').get()
        address = response.xpath('//span[contains(@class, "buy-content-title-address")]/text()').get()

        city_district_match = re.search(r'(\w+(?:市|縣))(\w+(?:區|鄉|鎮|市|鄉))', address)
        city = city_district_match.group(1) if city_district_match else '無'
        district = city_district_match.group(2) if city_district_match else '無'

        price = ''.join(response.xpath('//div[contains(@class, "buy-content-title-total-price")]/text()').getall())
        space = ' '.join(
            response.xpath('//div[contains(@class, "buy-content-detail-area")]/div/div/span/text()').getall())
        layout = response.xpath('//div[contains(@class, "buy-content-detail-layout")]/div/text()').get()
        age = ''.join(response.xpath('//div[contains(@class, "buy-content-detail-type")]/div/div/span/text()').getall())
        floors = response.xpath('//div[contains(@class, "buy-content-detail-floor")]/text()').get()
        community = ''.join(response.xpath('//div[contains(@class, "communityButton")]/span/text()').getall()).replace(
            '社區', '').strip()

        # Extract and format basic info
        basic_infos = response.xpath('//div[contains(@class, "buy-content-basic-cell")]')
        basic_info_dict = {}
        for basic_info in basic_infos:
            try:
                title = basic_info.xpath('.//div[contains(@class, "basic-title")]/text()').get().strip()
                value = basic_info.xpath('.//div[contains(@class, "basic-value")]/text()').get().strip()
                basic_info_dict[title] = value
            except:
                continue

        features = response.xpath(
            '//div[contains(@class, "buy-content-obj-feature")]//div[contains(@class, "description-cell-text")]/text()').getall()
        features_str = ' | '.join(features)

        images = response.xpath('//div[@class="carousel-thumbnail-img "]/img/@src').getall()

        # Extract data from embedded JSON
        script_text = response.xpath(
            '//script[contains(@id, "__NEXT_DATA__") and contains(@type, "application/json")]/text()').get()
        json_data = json.loads(script_text)

        lat = json_data['props']['initialReduxState']['buyReducer']['contentData']['latitude']
        lon = json_data['props']['initialReduxState']['buyReducer']['contentData']['longitude']

        trade_data = json_data['props']['initialReduxState']['buyReducer'].get('tradeData', {})
        life_info = json_data['props']['initialReduxState']['buyReducer']['detailData'].get('lifeInfo', [])
        utility_life_info = json_data['props']['initialReduxState']['buyReducer']['detailData'].get('utilitylifeInfo',
                                                                                                    [{}])

        site = '信義房屋'
        if response.xpath('//span[@class="buy-content-sameTrade"]/text()').get() == '非信義物件':
            source = response.xpath('//div[@class="buy-content-store-title"]/text()').get()
            site = f'信義房屋 ({source})'

        item = AididHouseItem(
            url=response.url,
            house_id=house_id,
            site=site,
            name=name,
            address=address,
            latitude=lat,
            longitude=lon,
            city=city,
            district=district,
            price=price,
            layout=layout,
            age=age,
            space=space,
            floors=floors,
            community=community,
            basic_info=basic_info_dict,  # JSON field
            features=features_str,
            life_info=life_info,  # JSON field
            utility_info=utility_life_info,  # JSON field
            review='',
            images=images,
            trade_data=trade_data  # JSON field
        )

        yield item
