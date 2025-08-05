import scrapy
from aidid_house.items import AididHouseItem, HouseUpdateItem
import re
import json


class BuyxinyiSpider(scrapy.Spider):
    name = "buyXinyi"
    allowed_domains = ["www.sinyi.com.tw"]

    # This will be populated by the pipeline
    existing_urls = set()

    cities = [
        "Taipei-city", 'NewTaipei-city', 'Keelung-city', 'Yilan-county', 'Hsinchu-city',
        'Hsinchu-county', 'Taoyuan-city', 'Miaoli-county', 'Taichung-city',
        'Changhua-county', 'Nantou-county', 'Yunlin-county', 'Chiayi-city', 'Chiayi-county',
        'Tainan-city', 'Kaohsiung-city', 'Pingtung-county', 'Penghu-county',
        'Taitung-county', 'Hualien-county', 'Kinmen-county',
    ]
    start_urls = [f"https://www.sinyi.com.tw/buy/list/{city}/default-desc/1" for city in cities]

    def parse(self, response):
        city = response.url.split('/')[-3]
        total_items_text = response.xpath('//div[contains(text(), "全部")]/text()').re_first(r'\((\d+)\)')

        if total_items_text:
            total_items = int(total_items_text)
            items_per_page = 20
            total_pages = (total_items + items_per_page - 1) // items_per_page

            self.logger.info(f"Found {total_pages} pages for {city} with {total_items} items.")
            for i in range(1, total_pages + 1):
                yield scrapy.Request(
                    f"https://www.sinyi.com.tw/buy/list/{city}/default-desc/{i}",
                    callback=self.parse_list_page
                )
        else:
            self.logger.warning(f"Could not find total pages for city: {city}. Scraping first page only.")
            yield from self.parse_list_page(response)

    def parse_list_page(self, response):
        urls = response.xpath('//div[contains(@class, "buy-list-item")]/a/@href').getall()
        for url_path in urls:
            full_url = response.urljoin(url_path)

            if full_url in self.existing_urls:
                # It's an existing house, just send an update signal
                yield HouseUpdateItem(url=full_url)
            else:
                # It's a new house, scrape the full details
                yield scrapy.Request(full_url, callback=self.parse_case_page)

    def parse_case_page(self, response):
        item = AididHouseItem(
            url=response.url, site='信義房屋', name='', address='', latitude=None, longitude=None,
            city='', district='', price='', layout='', age='', space='', floors='',
            community='', basic_info={}, features='', life_info=[], utility_info=[],
            review='', images=[], trade_data={}, house_id=''
        )

        try:
            # --- Safely extract data from embedded JSON ---
            script_text = response.xpath('//script[@id="__NEXT_DATA__"][@type="application/json"]/text()').get()
            if script_text:
                json_data = json.loads(script_text)
                buy_reducer = json_data.get('props', {}).get('initialReduxState', {}).get('buyReducer', {})
                content_data = buy_reducer.get('contentData', {})
                detail_data = buy_reducer.get('detailData', {})

                item['latitude'] = content_data.get('latitude')
                item['longitude'] = content_data.get('longitude')
                item['life_info'] = detail_data.get('lifeInfo', [])
                item['utility_info'] = detail_data.get('utilitylifeInfo', [])
                item['trade_data'] = buy_reducer.get('tradeData', {})

            # --- Safely extract data using XPath ---
            item['name'] = response.xpath('//span[contains(@class, "buy-content-title-name")]/text()').get(
                default='').strip()
            item['address'] = response.xpath('//span[contains(@class, "buy-content-title-address")]/text()').get(
                default='').strip()

            if item['address']:
                city_district_match = re.search(r'(\w+(?:市|縣))(\w+(?:區|鄉|鎮|市))', item['address'])
                if city_district_match:
                    item['city'] = city_district_match.group(1)
                    item['district'] = city_district_match.group(2)

            item['price'] = ''.join(
                response.xpath('//div[contains(@class, "buy-content-title-total-price")]/text()').getall()).strip()
            item['space'] = ' '.join(response.xpath(
                '//div[contains(@class, "buy-content-detail-area")]/div/div/span/text()').getall()).strip()
            item['layout'] = response.xpath('//div[contains(@class, "buy-content-detail-layout")]/div/text()').get(
                default='').strip()
            item['age'] = ''.join(response.xpath(
                '//div[contains(@class, "buy-content-detail-type")]/div/div/span/text()').getall()).strip()
            item['floors'] = response.xpath('//div[contains(@class, "buy-content-detail-floor")]/text()').get(
                default='').strip()
            item['community'] = ''.join(
                response.xpath('//div[contains(@class, "communityButton")]/span/text()').getall()).replace('社區',
                                                                                                           '').strip()

            basic_info_dict = {}
            for basic_info in response.xpath('//div[contains(@class, "buy-content-basic-cell")]'):
                title = basic_info.xpath('.//div[contains(@class, "basic-title")]/text()').get(default='').strip()
                value = basic_info.xpath('.//div[contains(@class, "basic-value")]/text()').get(default='').strip()
                if title:
                    basic_info_dict[title] = value
            item['basic_info'] = basic_info_dict

            item['features'] = ' | '.join(response.xpath(
                '//div[contains(@class, "buy-content-obj-feature")]//div[contains(@class, "description-cell-text")]/text()').getall())
            item['images'] = response.xpath('//div[contains(@class, "carousel-thumbnail-img")]/img/@src').getall()

            if response.xpath('//span[contains(@class, "buy-content-sameTrade")]/text()').get() == '非信義物件':
                source = response.xpath('//div[contains(@class, "buy-content-store-title")]/text()').get(default='')
                item['site'] = f'信義房屋 ({source})'

        except (json.JSONDecodeError, AttributeError, KeyError, TypeError) as e:
            self.logger.error(f"Error parsing case page {response.url}: {e}")

        yield item
