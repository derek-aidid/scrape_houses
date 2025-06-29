from itemadapter import ItemAdapter
import re
import json
import configparser
from datetime import datetime
import psycopg2
from psycopg2.extras import Json
import os
from aidid_house.items import SalesmanItem  # Ensure correct import path

def parse_sell_price(price):
    """
    Convert a price string like '1,314萬' to a numeric value.
    If the string contains '萬', multiply the numeric part by 10,000.
    Otherwise, return the float value.
    """
    if not price:
        return None
    price = price.strip().replace(',', '')
    if '萬' in price:
        num_str = price.replace('萬', '')
        try:
            num = float(num_str)
            return num
        except ValueError:
            return None
    else:
        try:
            return float(price)
        except ValueError:
            return None


def parse_building_space(space):
    """
    Extract the first numeric value from a space string.

    Examples:
      "建坪 25.75坪 / 地坪 30.55坪 主建物 25.75坪" -> returns 25.75
      "建坪 84.68坪 / 地坪 37.21坪 主  陽 84.68坪" -> returns 84.68
      "地坪 218.55坪 主建物 --" -> returns 218.55
      "建坪14.88" -> returns 14.88
      "建物24.15坪 主陽14.92 坪" -> returns 24.15

    If no number is found, returns None.
    """
    if not space:
        return None
    space = space.strip()
    # Match the first number (integer or decimal)
    match = re.search(r'([\d]+(?:\.[\d]+)?)', space)
    if match:
        try:
            return float(match.group(1))
        except ValueError:
            return None
    return None


# -------------------------------------------------------------------
# Pipeline for Cleaning Items
# -------------------------------------------------------------------
class AididHousePipeline:
    def process_item(self, item, spider):
        adapter = ItemAdapter(item)

        def clean_field(value):
            if isinstance(value, str):
                value = re.sub(r'[^\w\s,./|:;?!-]', '', value)
                value = re.sub(r'(\W)\1{2,}', r'\1', value)
            return value

        def format_price(price):
            """Format price to always show comma grouping and end with '萬'."""
            if not price:
                return price
            if not isinstance(price, str):
                price = str(price)
            price = price.strip()
            price = re.sub(r'\s+', '', price)
            if '萬' in price:
                num_str = price.replace('萬', '').replace(',', '')
                try:
                    num = int(num_str)
                except ValueError:
                    return price
                formatted = format(num, ",d")
                return f"{formatted}萬"
            else:
                num_str = price.replace(',', '')
                try:
                    num = int(num_str)
                except ValueError:
                    return price
                if len(num_str) < 6:
                    formatted = format(num, ",d")
                    return f"{formatted}萬"
                else:
                    result = num // 10000
                    formatted = format(result, ",d")
                    return f"{formatted}萬"

        # Process each field in the item.
        for field_name, value in adapter.items():
            if field_name == 'price':
                adapter[field_name] = format_price(value)
            elif field_name not in (
                    'url', 'community_info', 'rent_info',
                    'poi_info', 'images', 'trade_data',
                    'life_info', 'utility_info'
            ):
                adapter[field_name] = clean_field(value)
        return item


# -------------------------------------------------------------------
# Pipeline for Saving Items to PostgreSQL
# -------------------------------------------------------------------
class SaveToPostgresPipeline:
    config_path = os.path.join(os.path.dirname(__file__), 'config.ini')
    config = configparser.ConfigParser()
    config.read(config_path)

    def __init__(self):
        self.conn = psycopg2.connect(
            host=self.config['postgres']['host'],
            database=self.config['postgres']['database'],
            user=self.config['postgres']['user'],
            password=self.config['postgres']['password'],
            port=self.config['postgres']['port']
        )
        self.cur = self.conn.cursor()

        # Generate table name based on the current date
        self.table_name = f"houses_{datetime.now().strftime('%m_%d_%Y')}"
        self.config.set('postgres', 'table_name', self.table_name)
        with open(self.config_path, 'w') as configfile:
            self.config.write(configfile)
        print(f"Updated table_name in config.ini to: {self.table_name}")

        # Create the table without the house_id column
        self.cur.execute(f"""
        CREATE TABLE IF NOT EXISTS {self.table_name} (
            id SERIAL PRIMARY KEY,
            site TEXT,
            url TEXT,
            name TEXT,
            address TEXT,
            longitude DOUBLE PRECISION,
            latitude DOUBLE PRECISION,
            city TEXT,
            district TEXT,
            price TEXT,
            sell_price DOUBLE PRECISION,
            space TEXT,
            building_space DOUBLE PRECISION,
            layout TEXT,
            age TEXT,
            floors TEXT,
            community TEXT,
            basic_info JSONB,
            features TEXT,
            life_info JSONB,
            utility_info JSONB,
            review TEXT,
            images JSONB,
            trade_data JSONB
        )
        """)
        self.conn.commit()

        # Create indexes on the selected columns
        self.cur.execute(f"CREATE INDEX IF NOT EXISTS idx_site ON {self.table_name}(site);")
        self.conn.commit()
        self.cur.execute(f"CREATE INDEX IF NOT EXISTS idx_city ON {self.table_name}(city);")
        self.conn.commit()
        self.cur.execute(f"CREATE INDEX IF NOT EXISTS idx_district ON {self.table_name}(district);")
        self.conn.commit()
        self.cur.execute(f"CREATE INDEX IF NOT EXISTS idx_longitude ON {self.table_name}(longitude);")
        self.conn.commit()
        self.cur.execute(f"CREATE INDEX IF NOT EXISTS idx_latitude ON {self.table_name}(latitude);")
        self.conn.commit()

        print(f"Indexes on 'site', 'city', 'district', 'longitude', and 'latitude' created for table {self.table_name}.")

    def process_item(self, item, spider):
        adapter = ItemAdapter(item)

        # Process new numeric fields using our helper functions.
        sell_price_value = parse_sell_price(adapter.get('price'))
        building_space_value = parse_building_space(adapter.get('space'))

        # Serialize fields as JSON where needed.
        images = json.dumps(adapter.get('images')) if isinstance(adapter.get('images'), list) else adapter.get('images')
        basic_info = Json(adapter.get('basic_info')) if adapter.get('basic_info') else None
        life_info = Json(adapter.get('life_info')) if adapter.get('life_info') else None
        utility_info = Json(adapter.get('utility_info')) if adapter.get('utility_info') else None
        trade_data = Json(adapter.get('trade_data')) if adapter.get('trade_data') else None

        # Build the parameter tuple without house_id.
        params = (
            adapter.get('site'),
            adapter.get('url'),
            adapter.get('name'),
            adapter.get('address'),
            adapter.get('longitude'),
            adapter.get('latitude'),
            adapter.get('city'),
            adapter.get('district'),
            adapter.get('price'),
            sell_price_value,
            adapter.get('space'),
            building_space_value,
            adapter.get('layout'),
            adapter.get('age'),
            adapter.get('floors'),
            adapter.get('community'),
            basic_info,
            adapter.get('features'),
            life_info,
            utility_info,
            adapter.get('review'),
            images,
            trade_data
        )

        self.cur.execute(f"""
        INSERT INTO {self.table_name} (
            site, 
            url, 
            name, 
            address, 
            longitude, 
            latitude, 
            city, 
            district, 
            price, 
            sell_price,
            space, 
            building_space,
            layout, 
            age, 
            floors, 
            community, 
            basic_info, 
            features, 
            life_info, 
            utility_info, 
            review, 
            images, 
            trade_data
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
        )
        """, params)
        self.conn.commit()
        return item

    def close_spider(self, spider):
        self.cur.close()
        self.conn.close()
# ... (Other pipelines and helper functions if any) ...

class SaveSalesmanToPostgresPipeline:
    config_path = os.path.join(os.path.dirname(__file__), 'config.ini')
    config = configparser.ConfigParser()
    config.read(config_path)

    def __init__(self):
        self.conn = psycopg2.connect(
            host=self.config['postgres']['host'],
            database=self.config['postgres']['database'],
            user=self.config['postgres']['user'],
            password=self.config['postgres']['password'],
            port=self.config['postgres']['port']
        )
        self.cur = self.conn.cursor()
        self.table_name = f"salesman_info_{datetime.now().strftime('%m_%d_%Y')}"

        # Updated table creation statement
        self.cur.execute(f"""
        CREATE TABLE IF NOT EXISTS {self.table_name} (
            id SERIAL PRIMARY KEY,
            site TEXT,
            salesman TEXT,
            link TEXT, 
            brand_name TEXT,          
            store_name TEXT,          
            legal_company_name TEXT,  
            phone TEXT, 
            profile_image_url TEXT,   -- New Column
            property_url TEXT,
            CONSTRAINT uq_salesman_entry UNIQUE (site, property_url, salesman) 
        )
        """)
        self.conn.commit()
        print(f"Table {self.table_name} for salesman info ensured to exist with profile_image_url field.")

    def process_item(self, item, spider):
        if not isinstance(item, SalesmanItem):
            return item

        adapter = ItemAdapter(item)

        params = (
            adapter.get('site'),
            adapter.get('salesman'),
            adapter.get('link'),
            adapter.get('brand_name'),
            adapter.get('store_name'),
            adapter.get('legal_company_name'),
            adapter.get('phone'),
            adapter.get('profile_image_url'),  # New Field
            adapter.get('property_url')
        )

        try:
            # Updated INSERT statement
            self.cur.execute(f"""
            INSERT INTO {self.table_name} (
                site, salesman, link, 
                brand_name, store_name, legal_company_name, 
                phone, profile_image_url, property_url
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (site, property_url, salesman) DO NOTHING; 
            """, params)
            self.conn.commit()
        except psycopg2.Error as e:
            self.conn.rollback()
            spider.logger.error(f"DB Error inserting salesman item into {self.table_name}: {e.pgcode} - {e.pgerror}")
            spider.logger.error(f"Offending Item: {item}")
            spider.logger.error(f"SQL Params: {params}")
        except Exception as e:
            self.conn.rollback()
            spider.logger.error(f"Generic Error inserting salesman item into {self.table_name}: {e}")
            spider.logger.error(f"Offending Item: {item}")
            spider.logger.error(f"SQL Params: {params}")
        return item

    def close_spider(self, spider):
        if hasattr(self, 'cur') and self.cur and not self.cur.closed:
            self.cur.close()
        if hasattr(self, 'conn') and self.conn and not self.conn.closed:
            self.conn.close()