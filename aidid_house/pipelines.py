from itemadapter import ItemAdapter
import re
import json
import configparser
from datetime import datetime
import psycopg2
from psycopg2.extras import Json
import os
from scrapy.exceptions import DropItem
from aidid_house.items import AididHouseItem, HouseUpdateItem, RakuyaTradeItem


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
# Pipeline for Rakuya Trade Data with Master Table Support
# -------------------------------------------------------------------
class RakuyaTradePipeline:
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

        # Create the master table with all fields + data_status (支援新的統一欄位結構)
        self.cur.execute(f"""
        CREATE TABLE IF NOT EXISTS {self.master_table_name} (
            id SERIAL PRIMARY KEY,
            url TEXT UNIQUE NOT NULL,
            case_url TEXT,
            house_id TEXT,
            city_code INTEGER,
            city_name TEXT,
            area_name TEXT,
            zipcode TEXT,
            address TEXT,
            community_name TEXT,
            community_id INTEGER,
            community_url TEXT,
            property_type TEXT,
            sell_type_code TEXT,
            sell_type_code_short TEXT,
            total_area DECIMAL(10,2),
            price_per_ping DECIMAL(10,2),
            total_price DECIMAL(12,2),
            garage_size TEXT,
            garage_price TEXT,
            building_age DECIMAL(5,2),
            build_date TEXT,
            floor_info TEXT,
            trans_floor TEXT,
            sur_floor TEXT,
            building_floor TEXT,
            has_elevator BOOLEAN,
            bedrooms INTEGER,
            livingrooms INTEGER,
            bathrooms INTEGER,
            layout TEXT,
            main_size TEXT,
            sub_size TEXT,
            balcony_size TEXT,
            share_size TEXT,
            base_size TEXT,
            build_size TEXT,
            close_date TEXT,
            trade_count INTEGER,
            pay_type TEXT,
            memo TEXT,
            contract_memo TEXT,
            is_historical BOOLEAN DEFAULT FALSE,
            original_house_id TEXT,
            history_sequence INTEGER,
            history_data JSONB,
            is_special BOOLEAN,
            is_presale BOOLEAN,
            is_on_sale BOOLEAN,
            include_garage BOOLEAN,
            has_garage BOOLEAN,
            basic_info JSONB,
            trade_data JSONB,
            original_data JSONB,
            scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_seen DATE,
            data_status VARCHAR(10) DEFAULT 'ACTIVE'
        )
        """)
        
        self.conn.commit()  # 提交表創建
        spider.logger.info(f"成功創建或確認表 {self.master_table_name}")

        # Load existing active URLs (with error handling)
        try:
            self.cur.execute(f"SELECT url FROM {self.master_table_name} WHERE data_status = 'ACTIVE'")
            self.initial_active_urls = {row[0] for row in self.cur.fetchall()}
            spider.logger.info(f"Loaded {len(self.initial_active_urls)} active URLs from {self.master_table_name}.")
        except Exception as e:
            spider.logger.warning(f"無法載入現有 URLs，可能是新建的表: {e}")
            self.initial_active_urls = set()

        spider.existing_urls = self.initial_active_urls

    def process_item(self, item, spider):
        adapter = ItemAdapter(item)
        url = adapter.get('url')

        if isinstance(item, RakuyaTradeItem):
            self.live_urls.add(url)

            try:
                # Prepare data for insertion, correctly handling JSON fields
                insert_data = {}
                for field in adapter.field_names():
                    value = adapter.get(field)
                    # 檢查是否為需要 JSON 處理的欄位
                    if field in ['basic_info', 'trade_data', 'history_data', 'original_data']:
                        if value and isinstance(value, (dict, list)):
                            insert_data[field] = Json(value)
                        elif value:
                            insert_data[field] = Json(value)
                        else:
                            insert_data[field] = None
                    else:
                        # 處理其他可能包含字典的欄位
                        if isinstance(value, (dict, list)):
                            insert_data[field] = Json(value)
                        else:
                            insert_data[field] = value

                # Set scraped_at timestamp
                insert_data['scraped_at'] = datetime.now()
                insert_data['last_seen'] = datetime.now().date()

                # 動態生成 INSERT 語句以支援所有新欄位
                insert_data['data_status'] = 'ACTIVE'
                
                # 建立欄位列表和佔位符
                columns = list(insert_data.keys())
                placeholders = [f"%({col})s" for col in columns]
                update_columns = [f"{col} = EXCLUDED.{col}" for col in columns if col != 'url']
                
                insert_sql = f"""
                INSERT INTO {self.master_table_name} ({', '.join(columns)})
                VALUES ({', '.join(placeholders)})
                ON CONFLICT (url) DO UPDATE SET
                {', '.join(update_columns)}
                """
                
                self.cur.execute(insert_sql, insert_data)
                
                self.conn.commit()
                spider.logger.info(f"Inserted/Updated trade data for {adapter.get('address')}")
                
            except Exception as e:
                spider.logger.error(f"Error inserting trade data: {e}")
                self.conn.rollback()

        return item

    def close_spider(self, spider):
        # Mark inactive URLs
        inactive_urls = self.initial_active_urls - self.live_urls
        if inactive_urls:
            placeholders = ','.join(['%s'] * len(inactive_urls))
            self.cur.execute(f"""
            UPDATE {self.master_table_name} 
            SET data_status = 'INACTIVE' 
            WHERE url IN ({placeholders})
            """, list(inactive_urls))
            self.conn.commit()
            spider.logger.info(f"Marked {len(inactive_urls)} URLs as inactive")

        if self.cur:
            self.cur.close()
        if self.conn:
            self.conn.close()


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
        self.master_table_name = f"master_buyxinyi"

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
        
        # For other item types (like RakuyaTradeItem), pass through unchanged
        return item

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
