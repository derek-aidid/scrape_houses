import scrapy
from aidid_house.items import AididHouseItem
import json
import re
from urllib.parse import quote

class BuyHBSpider(scrapy.Spider):
    name = 'buyHB'
    allowed_domains = ['hbhousing.com.tw', 'api.map8.zone']
    start_urls = ['https://www.hbhousing.com.tw/BuyHouse/']

    def parse(self, response):
        url = 'https://www.hbhousing.com.tw/ajax/dataService.aspx?job=search&path=house&kv=false'

        for page_number in range(1, 10438):
            try:
                payload = {
                    'job': 'search',
                    'path': 'house',
                    'kv': 'false',
                    'q': f'2^1^^^^P^^^^^^^^^^^0^^0^1^{page_number}^0',
                    'rlg': '0'
                }

                yield scrapy.FormRequest(
                    url=url,
                    method='POST',
                    formdata=payload,
                    callback=self.parse_page,
                    meta={'page_number': page_number, "proxy": "https://derek5g:s2Ep_52qpMyjM6iNlv@dc.decodo.com:10000"}
                )

            except Exception as e:
                self.logger.error(f"An error occurred: {e}")
                break

    def parse_page(self, response):
        if response.status == 200:
            try:
                data = json.loads(response.text)
                houses = data.get('data')

                if houses:
                    for house in houses:
                        # Extract identifier to build URLs
                        sn = house.get('s')
                        case_url = f'https://www.hbhousing.com.tw/detail/?sn={sn}'
                        images = [f'https:{img}' for img in house.get('i', [])]

                        # Build map URL to fetch latitude and longitude
                        map_url = f'https://www.hbhousing.com.tw/Detail/map.aspx?sn={sn}'
                        yield scrapy.Request(
                            url=map_url,
                            callback=self.get_lat_lon,
                            meta={
                                'images': images,
                                'case_url': case_url,
                                "proxy": "https://derek5g:s2Ep_52qpMyjM6iNlv@dc.decodo.com:10000"
                            },
                        )
            except Exception as e:
                self.logger.error(f"Error parsing page data: {e}")

    def get_lat_lon(self, response):
        """
        Extracts latitude and longitude from the map page and continues processing.
        """
        images = response.meta.get('images', [])
        case_url = response.meta.get('case_url')
        lon, lat = None, None

        # Extract latitude and longitude using regex
        coord_match = re.search(r'lon=([\d.]+),lat=([\d.]+);', response.text)
        if coord_match:
            lon = float(coord_match.group(1))
            lat = float(coord_match.group(2))

        # Proceed to fetch detailed case info
        yield scrapy.Request(
            url=case_url,
            callback=self.parse_case_page,
            meta={
                'images': images,
                'lon': lon,
                'lat': lat,
                "proxy": "https://derek5g:s2Ep_52qpMyjM6iNlv@dc.decodo.com:10000"
            },
        )

    def parse_case_page(self, response):
        images = response.meta.get('images', [])
        lon = response.meta.get('lon')
        lat = response.meta.get('lat')

        name = response.xpath('//div[@class="item-info"]/p[@class="item_name"]/text()').get()
        address = response.xpath('//div[@class="item-info"]/p[@class="item_add"]/text()').get()
        address = address.strip() if address else None

        city_district_match = re.search(r'(\w+(?:市|縣))(\w+(?:區|鄉|鎮|市|鄉))', address) if address else None
        city = city_district_match.group(1) if city_district_match else '無'
        district = city_district_match.group(2) if city_district_match else '無'

        price = response.xpath('//div[@class="item_price"]/span[@class="hightlightprice"]/text()').get()
        price = price.strip().replace(',', '') if price else None

        space = response.xpath('//ul[@class="item_other"]/li[@class="icon_space"]/text()').get()
        space = space.strip() if space else None

        layout = response.xpath('//ul[@class="item_other"]/li[@class="icon_room"]/text()').get()
        layout = layout.strip() if layout else None

        age = response.xpath('//ul[@class="item_other"]/li[@class="icon_age"]/text()').get()
        age = age.strip() if age else None

        floors = response.xpath('//ul[@class="item_other"]/li[@class="icon_floor"]/text()').get()
        floors = floors.strip() if floors else None

        community = response.xpath('//tr[td[text()="社區"]]/td[2]/text()').get()
        community = community.strip() if community else '無'

        basic_info_box = response.xpath('//div[contains(@class, "basicinfo-box")]')
        basic_info = {}
        for element in basic_info_box.xpath('.//table//tr'):
            key = element.xpath('.//td[1]/text()').get()
            value = ''.join([t.strip() for t in element.xpath('.//td[2]//text()').getall() if t.strip()])
            if key and value:
                basic_info[key.strip()] = value

        features_elements = response.xpath('//ul[@class="features-other"]/li/text()').getall()
        features_str = ' | '.join([feature.strip() for feature in features_elements])

        # Create item without including any house-id field.
        item = AididHouseItem(
            url=response.url,
            site='住商',
            name=name,
            address=address,
            longitude=lon,
            latitude=lat,
            city=city,
            district=district,
            price=price,
            layout=layout,
            age=age,
            space=space,
            floors=floors,
            community=community,
            basic_info=basic_info,
            features=features_str,
            life_info=[],
            utility_info=[],
            review='',
            images=images,
        )

        yield item

    def errback_scrapy(self, failure):
        self.logger.error(repr(failure))
