from itemadapter import ItemAdapter
import configparser
from datetime import datetime
import psycopg2
import os
from aidid_house.items import SalesmanItem  # Ensure correct import path


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