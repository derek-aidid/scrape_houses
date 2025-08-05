from itemadapter import ItemAdapter
import re
import json
import configparser
from datetime import datetime
import psycopg2
from psycopg2.extras import Json
import os
from scrapy.exceptions import DropItem
from aidid_house.items import AididHouseItem, HouseUpdateItem


# -------------------------------------------------------------------
# Pipeline for Cleaning Items (Optional, can be disabled in settings if not needed)
# -------------------------------------------------------------------
class AididHousePipeline:
    def process_item(self, item, spider):
        # This pipeline only processes full AididHouseItem for data cleaning
        if not isinstance(item, AididHouseItem):
            return item
        # You can add any general cleaning logic here if needed in the future
        return item


# -------------------------------------------------------------------
# Main Delta Pipeline with Full Data Storage and Correct JSON Handling
# -------------------------------------------------------------------
class DeltaScrapePipeline:
    def __init__(self):
        self.conn = None
        self.cur = None
        self.master_table_name = None
        self.initial_active_urls = set()
        self.live_urls = set()

    def open_spider(self, spider):
        self.master_table_name = f"master_{spider.name.lower()}"

        config_path = os.path.join(os.path.dirname(__file__), 'config.ini')
        config = configparser.ConfigParser()
        config.read(config_path)

        self.conn = psycopg2.connect(
            host=config['postgres']['host'],
            database=config['postgres']['database'],
            user=config['postgres']['user'],
            password=config['postgres']['password'],
            port=config['postgres']['port']
        )
        self.cur = self.conn.cursor()

        # Create the master table with all original fields + data_status
        self.cur.execute(f"""
        CREATE TABLE IF NOT EXISTS {self.master_table_name} (
            id SERIAL PRIMARY KEY,
            url TEXT UNIQUE NOT NULL,
            site TEXT,
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
            trade_data JSONB,
            review TEXT,
            images JSONB,
            house_id TEXT,
            last_seen DATE,
            data_status VARCHAR(10) DEFAULT 'ACTIVE'
        )
        """)
        self.conn.commit()

        self.cur.execute(f"SELECT url FROM {self.master_table_name} WHERE data_status = 'ACTIVE'")
        self.initial_active_urls = {row[0] for row in self.cur.fetchall()}
        spider.logger.info(f"Loaded {len(self.initial_active_urls)} active URLs from {self.master_table_name}.")

        spider.existing_urls = self.initial_active_urls

    def process_item(self, item, spider):
        adapter = ItemAdapter(item)
        url = adapter.get('url')

        if isinstance(item, (AididHouseItem, HouseUpdateItem)):
            self.live_urls.add(url)

        if isinstance(item, AididHouseItem):
            # Prepare data for insertion, correctly handling JSON fields
            insert_data = {}
            for field in adapter.field_names():
                value = adapter.get(field)
                # Check if the field should be stored as JSON
                if field in ['basic_info', 'life_info', 'utility_info', 'trade_data', 'images']:
                    insert_data[field] = Json(value) if value else None
                else:
                    insert_data[field] = value

            insert_data['last_seen'] = datetime.now().date()
            insert_data['data_status'] = 'ACTIVE'

            # Build the UPSERT command to insert new records or update existing ones
            cols = ", ".join(insert_data.keys())
            placeholders = ", ".join(['%s'] * len(insert_data))
            update_cols = ", ".join([f"{col} = EXCLUDED.{col}" for col in insert_data.keys() if col != 'url'])

            sql = f"""
                INSERT INTO {self.master_table_name} ({cols})
                VALUES ({placeholders})
                ON CONFLICT (url) DO UPDATE SET {update_cols};
            """

            try:
                self.cur.execute(sql, list(insert_data.values()))
                self.conn.commit()
                spider.logger.info(f"Upserted full item: {url}")
            except Exception as e:
                self.conn.rollback()
                spider.logger.error(f"Failed to upsert item {url}: {e}")

            return item

        elif isinstance(item, HouseUpdateItem):
            # This is an existing, active item. Just update its timestamp.
            self.cur.execute(
                f"UPDATE {self.master_table_name} SET last_seen = %s WHERE url = %s",
                (datetime.now().date(), url)
            )
            self.conn.commit()
            raise DropItem(f"Updated last_seen for existing item: {url}")

    def close_spider(self, spider):
        spider.logger.info(
            f"Spider finished. Initial Active URLs: {len(self.initial_active_urls)}, Live URLs found: {len(self.live_urls)}")

        delisted_urls = self.initial_active_urls - self.live_urls

        if delisted_urls:
            spider.logger.info(f"Found {len(delisted_urls)} delisted URLs to mark as 'DELISTED'.")
            urls_tuple = tuple(delisted_urls)
            if len(urls_tuple) == 1:  # Psycopg2 needs a trailing comma for a single-element tuple
                urls_tuple = f"('{urls_tuple[0]}')"

            self.cur.execute(
                f"UPDATE {self.master_table_name} SET data_status = 'DELISTED' WHERE url IN {urls_tuple}"
            )
            self.conn.commit()
            spider.logger.info(
                f"Successfully marked {len(delisted_urls)} URLs as 'DELISTED' in {self.master_table_name}.")
        else:
            spider.logger.info("No active URLs were delisted in this run.")

        if self.cur: self.cur.close()
        if self.conn: self.conn.close()
