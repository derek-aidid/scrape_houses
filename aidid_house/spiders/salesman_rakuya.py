import scrapy
import re
import json
from urllib.parse import urlparse, parse_qs, urljoin
from aidid_house.items import SalesmanItem


class BuyrakuyaSalesmanSpider(scrapy.Spider):
    name = "buyRakuya_salesman"
    allowed_domains = ["www.rakuya.com.tw", "vip.rakuya.com.tw"]  # Keep vip for agentUrl
    # start_urls = [f"https://www.rakuya.com.tw/sell/result?city={i}" for i in range(1, 21)]
    start_urls = [f"https://www.rakuya.com.tw/sell/result?city={i}" for i in range(1, 21)]
    proxy = "https://dereksun:WrVt~x79Y0jGugas1r@gate.decodo.com:7000"

    custom_settings = {
        'ITEM_PIPELINES': {
            'aidid_house.pipelines.SaveSalesmanToPostgresPipeline': 300,
        }
        # Add other settings like USER_AGENT, DOWNLOAD_DELAY if needed
        # 'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        # 'DOWNLOAD_DELAY': 1,
    }

    def parse(self, response):
        script_content = response.css('script::text').re_first(r'window\.sellSearch\s*=\s*(\{.*?\});')
        if not script_content:
            return
        try:
            sell_search_data = json.loads(script_content)
            page_count = sell_search_data.get('pagination', {}).get('pageCount', 0)
            for page in range(1, page_count + 1):
                yield scrapy.Request(
                    url=f"{response.url}&page={page}",
                    callback=self.parse_pages,
                    meta={"proxy": "https://dereksun:WrVt~x79Y0jGugas1r@gate.decodo.com:7000"}
                )
        except json.JSONDecodeError as e:
            self.logger.error(f"Error parsing JSON: {e}")

    def parse_pages(self, response):
        for href in response.xpath('//div[@class="box__communityIntro"]/section/a/@href').getall():
            yield scrapy.Request(
                url=response.urljoin(href),
                callback=self.parse_property_page_for_salesman,
                meta={"proxy": "https://dereksun:WrVt~x79Y0jGugas1r@gate.decodo.com:7000"}
            )

    def parse_property_page_for_salesman(self, response):

        # Regex to find window.itemContact = {...}; making sure to capture the object correctly
        script_data_match = re.search(r'window\.itemContact\s*=\s*(\{.*?\});', response.text, re.DOTALL)

        json_str = script_data_match.group(1)

        try:
            contact_data = json.loads(json_str)
            seller_info = contact_data.get("sellerInfo")


            item = SalesmanItem()
            item['site'] = "樂屋網"
            item['salesman'] = seller_info.get("nick")

            phone_raw = seller_info.get("cellPhoneText")
            item['phone'] = phone_raw.replace('-', '').replace(' ', '') if phone_raw else None

            agent_url_raw = seller_info.get("agentUrl")
            if agent_url_raw:
                # Append /sell if it's a base VIP URL, consistent with previous requirement
                item['link'] = f"{agent_url_raw}/sell" if not agent_url_raw.endswith('/sell') else agent_url_raw
            else:
                item['link'] = None

            item['brand_name'] = seller_info.get("companyName")  # e.g., "21世紀不動產"

            store_name_parts = []
            franchise_type = seller_info.get("franchiseType")  # e.g., "加盟"
            branch_name = seller_info.get("branch")  # e.g., "新莊頭前雙捷運加盟店"
            if franchise_type and branch_name:
                store_name_parts.append(f"【{franchise_type}】{branch_name}")
            elif branch_name:  # If no franchiseType, just use branch
                store_name_parts.append(branch_name)
            item['store_name'] = "".join(store_name_parts) if store_name_parts else None

            item['legal_company_name'] = seller_info.get("franchiseName")  # e.g., "伸億不動產仲介經紀有限公司"
            item['profile_image_url'] = seller_info.get("image")
            item['property_url'] = response.url

            if item['salesman'] or item['phone']:  # Yield if we have a name or phone
                yield item
            else:
                self.logger.warning(
                    f"Not enough salesman data in window.itemContact on {response.url} (Salesman: {item['salesman']}, Phone: {item['phone']})")

        except json.JSONDecodeError as e:
            self.logger.error(
                f"Failed to parse JSON from window.itemContact on {response.url}: {e}. JSON string was: {json_str[:500]}...")  # Log part of the string
        except Exception as e:
            self.logger.error(f"Unexpected error parsing window.itemContact on {response.url}: {e}")