import mysql.connector
from itemadapter import ItemAdapter
import re
import json
import configparser
from datetime import datetime
import psycopg2
from psycopg2.extras import Json




class AididHousePipeline:
    def process_item(self, item, spider):
        adapter = ItemAdapter(item)

        def clean_field(value):
            if isinstance(value, str):
                value = re.sub(r'[^\w\s,./|:;?!-]', '', value)
                value = re.sub(r'(\W)\1{2,}', r'\1', value)
            return value

        for field_name, value in adapter.items():
            if field_name not in ('url', 'community_info', 'rent_info', 'poi_info', 'images', 'trade_data', 'life_info', 'utility_info'):  # Skip cleaning for images
                adapter[field_name] = clean_field(value)

        return item

class SaveToPostgresPipeline:
    config = configparser.ConfigParser()
    config.read('config.ini')
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

        # Create the table if it does not exist
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
            space TEXT,
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
            trade_data JSONB,
            house_id TEXT UNIQUE
        )
        """)
        self.conn.commit()

    def process_item(self, item, spider):
        adapter = ItemAdapter(item)

        # Serialize fields as JSON where needed
        images = json.dumps(adapter.get('images')) if isinstance(adapter.get('images'), list) else adapter.get('images')
        basic_info = Json(adapter.get('basic_info')) if adapter.get('basic_info') else None
        life_info = Json(adapter.get('life_info')) if adapter.get('life_info') else None
        utility_info = Json(adapter.get('utility_info')) if adapter.get('utility_info') else None
        trade_data = Json(adapter.get('trade_data')) if adapter.get('trade_data') else None

        # Insert item into the database
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
            adapter.get('space'),
            adapter.get('layout'),
            adapter.get('age'),
            adapter.get('floors'),
            adapter.get('community'),
            basic_info,
            adapter.get('features'),
            life_info,
            utility_info,
            adapter.get('review'),
            images,  # Store as JSON
            trade_data,
            adapter.get('house_id')
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
            space, 
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
            trade_data, 
            house_id
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
        ) ON CONFLICT (house_id) DO NOTHING
        """, params)

        self.conn.commit()
        return item

    def close_spider(self, spider):
        self.cur.close()
        self.conn.close()
