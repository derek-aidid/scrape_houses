import re
import json
import scrapy
from aidid_house.items import AididHouseItem, HouseUpdateItem


class BuyyongchingSpider(scrapy.Spider):
    name = "buyYungChing"
    allowed_domains = ["buy.yungching.com.tw"]
    
    # This will be populated by the pipeline
    existing_urls = set()
    
    areas = [
        "台北市", "新北市", "桃園市", "台中市", "台南市", "高雄市", "基隆市", "新竹市", "嘉義市", "宜蘭縣",
        "新竹縣", "苗栗縣", "彰化縣", "南投縣", "雲林縣", "嘉義縣", "屏東縣", "花蓮縣", "台東縣",
        "澎湖縣", "金門縣", "連江縣"
    ]
    start_urls = [f"https://buy.yungching.com.tw/list/{city}-_c" for city in areas]

    def parse(self, response):
        # Start with the first page
        yield scrapy.Request(
            response.url,
            callback=self.parse_list_page,
            meta={"proxy": "https://dereksun:L4m2_7cFdsl0GAaepi@gate.decodo.com:7000"}
        )

    def parse_list_page(self, response):
        # Extract URLs from current page
        urls = response.xpath('//yc-ng-buy-house-card/a/@href').getall()
        for url in urls:
            # Ensure we have a complete URL
            if url.startswith('house/'):
                # Convert relative path to absolute URL
                full_url = f"https://buy.yungching.com.tw/{url}"
            else:
                full_url = response.urljoin(url)
            
            if full_url in self.existing_urls:
                # It's an existing house, just send an update signal
                yield HouseUpdateItem(url=full_url)
            else:
                # It's a new house, scrape the full details
                yield scrapy.Request(
                    full_url,
                    callback=self.parse_case_page,
                    meta={"proxy": "https://dereksun:L4m2_7cFdsl0GAaepi@gate.decodo.com:7000"}
                )
        
        # Check if there's a next page button
        next_page_button = response.xpath('//div[contains(@class, "paginationNext")]')
        if next_page_button:
            # Extract current page number from URL
            current_page = 1
            if 'pg=' in response.url:
                page_match = re.search(r'pg=(\d+)', response.url)
                if page_match:
                    current_page = int(page_match.group(1))
            
            next_page = current_page + 1
            next_url = f"{response.url.split('?')[0]}?pg={next_page}"
            
            yield scrapy.Request(
                next_url,
                callback=self.parse_list_page,
                meta={"proxy": "https://dereksun:L4m2_7cFdsl0GAaepi@gate.decodo.com:7000"}
            )

    def parse_case_page(self, response):
        try:
            # Extract house_id from URL
            house_id = response.url.split('/')[-1]
            self.logger.info(f"Extracted house_id: {house_id}")
            
            # Extract basic information using XPath
            name = response.xpath('//h1/text()').get('').strip()
            if not name:
                name = response.xpath('//h1//text()').get('').strip()
            
            # Extract address
            address = response.xpath('//h3[contains(text(), "台北市") or contains(text(), "新北市") or contains(text(), "桃園市") or contains(text(), "台中市") or contains(text(), "台南市") or contains(text(), "高雄市") or contains(text(), "基隆市") or contains(text(), "新竹市") or contains(text(), "嘉義市") or contains(text(), "宜蘭縣") or contains(text(), "新竹縣") or contains(text(), "苗栗縣") or contains(text(), "彰化縣") or contains(text(), "南投縣") or contains(text(), "雲林縣") or contains(text(), "嘉義縣") or contains(text(), "屏東縣") or contains(text(), "花蓮縣") or contains(text(), "台東縣") or contains(text(), "澎湖縣") or contains(text(), "金門縣") or contains(text(), "連江縣")]/text()').get('').strip()
            
            # Extract city and district from address using buyXinyi method
            city = ''
            district = ''
            if address:
                import re
                city_district_match = re.search(r'(\w+(?:市|縣))(\w+(?:區|鄉|鎮|市))', address)
                if city_district_match:
                    city = city_district_match.group(1)
                    district = city_district_match.group(2)
            
            # Extract price - corrected XPath
            price = response.xpath('//div[contains(@class, "price")]/text()').get('').strip()
            if not price:
                price = response.xpath('//span[contains(@class, "price")]/text()').get('').strip()
            if not price:
                # Try to get price from the specific structure
                price_text = response.xpath('//div[contains(@class, "discount-and-price-wrapper")]//div[contains(@class, "price")]/text()').get('').strip()
                if price_text:
                    price = price_text + '萬'
            
            # Extract space - corrected for the specific structure
            space = response.xpath('//span[contains(text(), "建物") and contains(text(), "坪")]/text()').re_first(r'建物(\d+\.?\d*)\s*坪')
            if not space:
                space = response.xpath('//span[contains(text(), "坪")]/text()').re_first(r'(\d+\.?\d*)\s*坪')
            if space:
                space = f"{space}坪"
            
            # Extract layout - corrected for the specific structure
            layout = response.xpath('//div[contains(@class, "room")]/text()').get('').strip()
            if not layout:
                layout = response.xpath('//span[contains(@class, "room")]/text()').get('').strip()
            
            # Extract age
            age = response.xpath('//div[contains(text(), "年")]/text()').re_first(r'(\d+\.?\d*)\s*年')
            if not age:
                age = response.xpath('//span[contains(text(), "年")]/text()').re_first(r'(\d+\.?\d*)\s*年')
            
            # Extract floors
            floors = response.xpath('//div[contains(text(), "樓")]/text()').re_first(r'(\d+/\d+樓)')
            if not floors:
                floors = response.xpath('//span[contains(text(), "樓")]/text()').re_first(r'(\d+/\d+樓)')
            
            # Extract community - corrected for the specific structure
            community = response.xpath('//a[contains(@class, "community")]/h3/text()').get('').strip()
            if not community:
                community = response.xpath('//a[contains(@href, "/community/")]/text()').get('').strip()
            if not community:
                community = response.xpath('//div[contains(text(), "社區")]/text()').get('').strip()
            
            # Extract features
            features = response.xpath('//div[contains(@class, "tag") or contains(@class, "feature")]/text()').getall()
            features_text = ', '.join([f.strip() for f in features if f.strip()])
            
            # Extract images
            images = response.xpath('//img[contains(@src, "yccdn.yungching.com.tw")]/@src').getall()
            
            # Extract basic_info (try to get from page content)
            basic_info = {}
            basic_info_sections = response.xpath('//div[contains(@class, "basic") or contains(@class, "info")]//text()').getall()
            if basic_info_sections:
                basic_info = {'raw_text': ' '.join([t.strip() for t in basic_info_sections if t.strip()])}
            
            # Extract review (try to get from page content)
            review = response.xpath('//div[contains(@class, "review") or contains(@class, "comment")]/text()').get('').strip()
            if not review:
                review = response.xpath('//p[contains(@class, "description")]/text()').get('').strip()
            
            # Extract trade_data (try to get from page content)
            trade_data = {}
            trade_info = response.xpath('//div[contains(text(), "成交") or contains(text(), "交易")]/text()').getall()
            if trade_info:
                trade_data = {'raw_text': ' '.join([t.strip() for t in trade_info if t.strip()])}
            
            # Extract coordinates (try to get from page content or meta tags)
            latitude = ''
            longitude = ''
            lat_meta = response.xpath('//meta[@name="latitude"]/@content').get()
            lng_meta = response.xpath('//meta[@name="longitude"]/@content').get()
            if lat_meta and lng_meta:
                latitude = lat_meta
                longitude = lng_meta
            
            # Log extracted data
            self.logger.info(f"Successfully extracted data for {house_id}")
            self.logger.info(f"House name: {name}")
            self.logger.info(f"Address: {address}")
            self.logger.info(f"City: {city}")
            self.logger.info(f"District: {district}")
            self.logger.info(f"Price: {price}")
            self.logger.info(f"Layout: {layout}")
            self.logger.info(f"Age: {age}")
            self.logger.info(f"Space: {space}")
            self.logger.info(f"Floors: {floors}")
            self.logger.info(f"Community: {community}")
            self.logger.info(f"Features: {features_text}")
            self.logger.info(f"Images count: {len(images)}")
            
            # Create the item with all fields from items.py
            item = AididHouseItem(
                url=response.url,
                site='永慶房屋',
                name=name,
                address=address,
                longitude=longitude,
                latitude=latitude,
                city=city,
                district=district,
                price=price,
                space=space,
                layout=layout,
                age=age,
                floors=floors,
                community=community,
                basic_info=basic_info,
                features=features_text,
                life_info=[],  # Will be populated by parse_poi_data
                utility_info=[],  # Will be populated by parse_poi_data
                trade_data=trade_data,
                review=review,
                images=images,
                house_id=house_id
            )

            # Prepare POI API request
            if house_id:
                poi_api_url = f"https://buy.yungching.com.tw/api/v2/information/poi?id={house_id}"
                yield scrapy.Request(
                    poi_api_url,
                    callback=self.parse_poi_data,
                    meta={"item": item, "proxy": "https://dereksun:L4m2_7cFdsl0GAaepi@gate.decodo.com:7000"}
                )
            else:
                # If no house_id, yield the item without POI data
                yield item

        except Exception as e:
            self.logger.error(f"Error parsing case page {response.url}: {e}")

    def parse_poi_data(self, response):
        item = response.meta["item"]
        try:
            pois = json.loads(response.text).get("data", {}).get("pois", [])
            life_categories = {"休閒娛樂", "超商", "停車場", "購物"}
            utility_categories = {"交通", "醫療", "政府", "學校"}

            life_list, util_list = [], []
            
            # Extract coordinates from first available POI
            latitude = ''
            longitude = ''
            
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
                    
                    # Extract coordinates from first POI if not already set
                    if not latitude and detail.get("poiLat"):
                        latitude = round(detail.get("poiLat"), 3)
                    if not longitude and detail.get("poiLng"):
                        longitude = round(detail.get("poiLng"), 3)
                    
                    if cat in life_categories:
                        life_list.append(entry)
                    elif cat in utility_categories:
                        util_list.append(entry)

            item["life_info"] = life_list
            item["utility_info"] = util_list
            
            # Update coordinates if found
            if latitude:
                item["latitude"] = latitude
            if longitude:
                item["longitude"] = longitude
                
            self.logger.info(f"Updated coordinates for {item['house_id']}: lat={latitude}, lng={longitude}")
            
        except Exception as e:
            self.logger.error(f"Error parsing POI data: {e}")

        # Finally, yield the enriched item
        yield item
