import scrapy
import json
import math
from datetime import datetime
from aidid_house.items import RakuyaTradeItem

class RakuyaTradesSpider(scrapy.Spider):
    name = 'rakuya_trades'
    allowed_domains = ['rakuya.com.tw']

    # 代理設定
    # proxy_meta = {"proxy": "https://derek5g:QnpyfBLz4cxpx1Z@gate.decodo.com:10000"}
    proxy_meta = {"proxy": "http://dc.decodo.com:10000"}

    # 城市代碼對應表
    city_mapping = {
        0: '台北市',
        1: '基隆市',
        2: '新北市', 
        3: '宜蘭縣',
        4: '桃園市',
        5: '新竹市',
        6: '新竹縣',
        7: '苗栗縣',
        8: '台中市',
        9: '彰化縣',
        10: '南投縣',
        11: '雲林縣',
        12: '嘉義市',
        13: '嘉義縣',
        14: '台南市',
        15: '高雄市',
        16: '澎湖縣',
        17: '屏東縣',
        18: '台東縣',
        19: '花蓮縣',
        20: '金門連江'
    }

    def start_requests(self):
        """生成所有城市的第一頁請求"""
        # 爬取所有城市 (0-20)
        for city_code in range(21):  # 0 到 20
            api_url = f"https://www.rakuya.com.tw/realprice/realprice_sell_search/get-result?city={city_code}&sort=11&page=1"
            
            yield scrapy.Request(
                url=api_url,
                callback=self.parse_first_page,
                meta={
                    'city_code': city_code,
                    'city_name': self.city_mapping.get(city_code, f'城市{city_code}'),
                    **self.proxy_meta
                }
            )

    def parse_first_page(self, response):
        """解析第一頁，計算總頁數並生成所有頁面的請求"""
        city_code = response.meta['city_code']
        city_name = response.meta['city_name']
        
        try:
            data = json.loads(response.text)
            deal_total = data.get('dealTotal', 0)
            
            if deal_total == 0:
                self.logger.warning(f"{city_name} 沒有找到任何交易資料")
                return
            
            # 計算總頁數：dealTotal / 20 + 1
            total_pages = math.ceil(deal_total / 20)
            self.logger.info(f"{city_name} 總共 {deal_total} 筆交易，{total_pages} 頁")
            
            # 生成所有頁面的請求
            for page in range(1, total_pages + 1):
                api_url = f"https://www.rakuya.com.tw/realprice/realprice_sell_search/get-result?city={city_code}&sort=11&page={page}"
                
                yield scrapy.Request(
                    url=api_url,
                    callback=self.parse_page_data,
                    meta={
                        'city_code': city_code,
                        'city_name': city_name,
                        'page': page,
                        'total_pages': total_pages,
                        **self.proxy_meta
                    }
                )
                
        except json.JSONDecodeError as e:
            self.logger.error(f"解析 {city_name} 第一頁 JSON 失敗: {e}")

    def parse_page_data(self, response):
        """解析每頁的交易資料"""
        city_code = response.meta['city_code']
        city_name = response.meta['city_name']
        page = response.meta['page']
        
        try:
            data = json.loads(response.text)
            deal_list = data.get('dealList', [])
            format_deal_list = data.get('formatDealList', [])
            
            self.logger.info(f"解析 {city_name} 第 {page} 頁：dealList={len(deal_list)}, formatDealList={len(format_deal_list)}")
            
            # 合併兩個列表的資料，去除重複
            merged_deals = self.merge_deal_data(deal_list, format_deal_list)
            
            # 為每筆交易創建 Item，並處理歷史交易
            for deal_data in merged_deals:
                # 檢查是否有歷史交易資料
                history_count = deal_data.get('history_total', 1)
                house_id = deal_data.get('house_id')
                
                if history_count > 1 and house_id:
                    # 如果有歷史交易，發送請求獲取歷史詳情，延遲創建 Item
                    history_url = f"https://www.rakuya.com.tw/realprice/api/info/history?sn={house_id}"
                    yield scrapy.Request(
                        url=history_url,
                        callback=self.parse_history_data,
                        meta={
                            'house_id': house_id,
                            'city_code': city_code,
                            'city_name': city_name,
                            'main_item_data': deal_data,
                            **self.proxy_meta
                        }
                    )
                elif house_id:
                    # 有 house_id 但沒有歷史交易，仍然嘗試獲取歷史資料以確保資料完整性
                    # 但設定較低的優先級，避免過度請求
                    history_url = f"https://www.rakuya.com.tw/realprice/api/info/history?sn={house_id}"
                    yield scrapy.Request(
                        url=history_url,
                        callback=self.parse_history_data,
                        meta={
                            'house_id': house_id,
                            'city_code': city_code,
                            'city_name': city_name,
                            'main_item_data': deal_data,
                            'force_create': True,  # 強制創建 Item
                            **self.proxy_meta
                        },
                        priority=1  # 較低優先級
                    )
                else:
                    # 沒有 house_id，直接創建 Item
                    item = self.create_trade_item(deal_data, city_code, city_name)
                    yield item
                
        except json.JSONDecodeError as e:
            self.logger.error(f"解析 {city_name} 第 {page} 頁 JSON 失敗: {e}")

    def merge_deal_data(self, deal_list, format_deal_list):
        """合併 dealList 和 formatDealList，去除重複並保留所有有用欄位"""
        # 欄位對應表：將相同值的不同欄位名統一
        field_mapping = {
            # 基本識別
            'dealId': 'house_id',          # dealList.dealId = formatDealList.sn
            'sn': 'house_id',
            
            # 地址資訊
            'addr': 'address',             # dealList.addr = formatDealList.address
            'addrBuNo': 'address',         # 也對應到 address
            
            # 區域資訊
            'zipcodeArea': 'area_name',    # dealList.zipcodeArea = formatDealList.areaName
            'areaName': 'area_name',
            
            # 社區名稱
            'community': 'community_name', # dealList.community = formatDealList.communityName
            'communityName': 'community_name',
            
            # URL
            'realpriceDetailUrl': 'detail_url',  # dealList.realpriceDetailUrl = formatDealList.url
            'url': 'detail_url',
            
            # 樓層資訊
            'transFloor': 'trans_floor',   # dealList.transFloor = formatDealList.transFloors
            'transFloors': 'trans_floor',
            'surFloor': 'sur_floor',       # dealList.surFloor = formatDealList.surFloors
            'surFloors': 'sur_floor',
            'buildingFloor': 'building_floor', # dealList.buildingFloor = formatDealList.buildingFloors
            'buildingFloors': 'building_floor',
            
            # 歷史交易次數
            'snGrountCnt': 'history_total', # dealList.snGrountCnt = formatDealList.historyTotal
            'historyTotal': 'history_total',
            
            # 面積（某些情況下相同）
            'garageSize': 'garage_size',   # 統一車位面積
            'totalSize': 'total_size',     # 統一總面積
        }
        
        # 建立以 house_id 為 key 的字典
        merged_dict = {}
        
        # 處理 dealList
        for deal in deal_list:
            normalized_deal = self.normalize_fields(deal, field_mapping)
            house_id = normalized_deal.get('house_id')
            if house_id:
                merged_dict[house_id] = normalized_deal
        
        # 合併 formatDealList
        for format_deal in format_deal_list:
            normalized_format = self.normalize_fields(format_deal, field_mapping)
            house_id = normalized_format.get('house_id')
            if house_id:
                if house_id in merged_dict:
                    # 合併資料，避免覆蓋已有的有效值
                    for key, value in normalized_format.items():
                        if key not in merged_dict[house_id] or not merged_dict[house_id][key]:
                            merged_dict[house_id][key] = value
                        # 保留原始欄位名稱以供參考
                        elif key in merged_dict[house_id] and merged_dict[house_id][key] != value:
                            # 如果值不同，保留兩個版本
                            alt_key = f"{key}_alt"
                            merged_dict[house_id][alt_key] = value
                else:
                    # 新的記錄
                    merged_dict[house_id] = normalized_format
        
        return list(merged_dict.values())
    
    def normalize_fields(self, data, field_mapping):
        """根據欄位對應表統一欄位名稱"""
        normalized = {}
        original_data = {}
        
        for original_key, value in data.items():
            # 使用對應表中的統一名稱，如果沒有對應則保持原名
            unified_key = field_mapping.get(original_key, original_key)
            
            # 如果統一名稱已存在且值不同，保留原始值作為備用
            if unified_key in normalized and normalized[unified_key] != value and value:
                alt_key = f"{unified_key}_from_{original_key}"
                normalized[alt_key] = value
            elif value or unified_key not in normalized:
                normalized[unified_key] = value
            
            # 保留原始資料結構
            original_data[original_key] = value
        
        # 添加原始資料引用
        normalized['_original_data'] = original_data
        return normalized

    def create_trade_item(self, deal_data, city_code, city_name):
        """從合併的交易資料創建 RakuyaTradeItem"""
        item = RakuyaTradeItem()
        
        # 基本識別資訊（使用統一後的欄位名）
        item['house_id'] = deal_data.get('house_id', '')
        case_url = deal_data.get('detail_url', '')
        item['case_url'] = case_url
        item['url'] = case_url  # pipeline 需要這個欄位
        item['city_code'] = city_code
        item['city_name'] = deal_data.get('cityName') or city_name
        
        # 地址資訊（使用統一後的欄位名）
        item['address'] = deal_data.get('address', '')
        item['community_name'] = deal_data.get('community_name', '')
        item['area_name'] = deal_data.get('area_name', '')
        item['zipcode'] = deal_data.get('zipcode', '')
        item['community_id'] = deal_data.get('communityId', 0)
        item['community_url'] = deal_data.get('communityUrl', '')
        
        # 房屋類型
        item['property_type'] = deal_data.get('sellType', '')
        item['sell_type_code'] = deal_data.get('sellTypeCode', '')
        item['sell_type_code_short'] = deal_data.get('sellTypeCodeShort', '')
        
        # 價格資訊
        close_price = deal_data.get('closePrice', '0')
        unit_price = deal_data.get('unitPrice', '0')
        
        # 清理價格字符串，移除逗號
        if isinstance(close_price, str):
            close_price = close_price.replace(',', '')
        if isinstance(unit_price, str):
            unit_price = unit_price.replace(',', '')
            
        try:
            item['total_price'] = float(close_price) if close_price else 0.0
            item['price_per_ping'] = float(unit_price) if unit_price else 0.0
        except (ValueError, TypeError):
            item['total_price'] = 0.0
            item['price_per_ping'] = 0.0
        
        # 面積資訊
        total_size = deal_data.get('total_size', 0)
        try:
            item['total_area'] = float(total_size) if total_size else 0.0
        except (ValueError, TypeError):
            item['total_area'] = 0.0
        
        # 車位資訊
        item['garage_size'] = deal_data.get('garage_size', '')
        item['garage_price'] = deal_data.get('garagePrice', '')
        
        # 建築年齡
        build_year = deal_data.get('buildYear', '').replace('年', '')
        try:
            item['building_age'] = float(build_year) if build_year else 0.0
        except (ValueError, TypeError):
            item['building_age'] = 0.0
        
        # 建築資訊
        item['build_date'] = deal_data.get('builddate', '')
        item['has_elevator'] = deal_data.get('hasElevator', False)
        
        # 樓層資訊（使用統一後的欄位名）
        trans_floor = deal_data.get('trans_floor', '')
        sur_floor = deal_data.get('sur_floor', '')
        item['floor_info'] = f"{trans_floor}/{sur_floor}" if trans_floor and sur_floor else deal_data.get('building_floor', '')
        item['trans_floor'] = trans_floor
        item['sur_floor'] = sur_floor
        item['building_floor'] = deal_data.get('building_floor', '')
        
        # 房間配置（處理 "3房" 格式）
        bedrooms_str = str(deal_data.get('bedrooms', '0'))
        try:
            item['bedrooms'] = int(bedrooms_str.replace('房', '').replace('室', '')) if bedrooms_str and bedrooms_str != '0' else 0
        except (ValueError, TypeError):
            item['bedrooms'] = 0
            
        livingrooms_str = str(deal_data.get('livingrooms', '0'))
        try:
            item['livingrooms'] = int(livingrooms_str.replace('廳', '').replace('室', '')) if livingrooms_str and livingrooms_str != '0' else 0
        except (ValueError, TypeError):
            item['livingrooms'] = 0
            
        bathrooms_str = str(deal_data.get('bathrooms', '0'))
        try:
            item['bathrooms'] = int(bathrooms_str.replace('衛', '').replace('浴', '')) if bathrooms_str and bathrooms_str != '0' else 0
        except (ValueError, TypeError):
            item['bathrooms'] = 0
        item['layout'] = deal_data.get('layout', '')
        
        # 面積詳細資訊
        item['main_size'] = deal_data.get('mainSize', '')
        item['sub_size'] = deal_data.get('subSize', '')
        item['balcony_size'] = deal_data.get('balconySize', '')
        item['share_size'] = deal_data.get('shareSize', '')
        item['base_size'] = deal_data.get('baseSize', '')
        item['build_size'] = deal_data.get('buildSize', '')
        
        # 交易資訊
        item['close_date'] = deal_data.get('closeDate', '')
        item['trade_count'] = deal_data.get('history_total', 1)
        item['pay_type'] = deal_data.get('payType', '')
        item['memo'] = deal_data.get('memo', '')
        item['contract_memo'] = deal_data.get('contractMemo', '')
        
        # 歷史交易支援
        item['is_historical'] = deal_data.get('is_historical', False)
        item['original_house_id'] = deal_data.get('original_house_id', '')
        item['history_sequence'] = deal_data.get('history_sequence', 0)
        # 初始化 history_data 為 None，讓 parse_history_data 來設定
        item['history_data'] = None
        
        # 狀態標記
        item['is_special'] = deal_data.get('isSpecial', False)
        item['is_presale'] = deal_data.get('isPresale', False)
        item['is_on_sale'] = deal_data.get('isOnSale', False)
        item['include_garage'] = deal_data.get('includeGarage', False)
        item['has_garage'] = deal_data.get('hasGarage', False)
        
        # 完整資料保存
        item['trade_data'] = {
            'close_date': item['close_date'],
            'total_price': item['total_price'],
            'price_per_ping': item['price_per_ping'],
            'total_area': item['total_area'],
            'building_age': item['building_age'],
            'floor_info': item['floor_info']
        }
        
        # 基本資訊 (保持向後相容性)
        item['basic_info'] = {
            'garage_type': deal_data.get('garage', ''),
            'garage_size_desc': deal_data.get('garageSizeDesc', ''),
            'garage_price_desc': deal_data.get('garagePriceDesc', ''),
            'unit_price_garage_desc': deal_data.get('unitPriceGarageDesc', ''),
            'trans_floors_list': deal_data.get('transFloorsList', []),
            'trans_floors_short_desc': deal_data.get('transFloorsShortDesc', ''),
            'type_code': deal_data.get('typecode', ''),
            'unit_price_exclude_garage': deal_data.get('unitPriceExcludeGarage', False),
            'uint_price_exclude_garage': deal_data.get('uintPriceExcludeGarage', False),
            'is_show_include_parking': deal_data.get('isShowIncludeParking', False),
            'building_no': deal_data.get('buildingNo', ''),
            'addr_bu_no': deal_data.get('addrBuNo', ''),
            'addr_zipcode': deal_data.get('addrZipcode', ''),
            'pattern': deal_data.get('pattern', ''),
            'realprice_sell_cnt_url': deal_data.get('realpriceSellCntUrl', ''),
            'building_age_desc': deal_data.get('buildingAge', ''),
        }
        
        # 原始資料完整保存
        item['original_data'] = deal_data.get('_original_data', deal_data)
        
        # 時間戳記
        item['scraped_at'] = datetime.now().isoformat()
        item['last_seen'] = datetime.now().isoformat()
        item['data_status'] = 'ACTIVE'
        
        return item
    
    def parse_history_data(self, response):
        """解析歷史交易資料 - 使用新的歷史 API"""
        house_id = response.meta['house_id']
        city_code = response.meta['city_code']
        city_name = response.meta['city_name']
        main_item_data = response.meta['main_item_data']
        force_create = response.meta.get('force_create', False)
        
        try:
            # 解析新的歷史 API 響應格式
            history_response = json.loads(response.text)
            
            # 檢查 API 響應狀態
            if not history_response.get('status'):
                self.logger.warning(f"房屋 {house_id} 歷史 API 返回錯誤: {history_response.get('message', '未知錯誤')}")
                # 即使 API 錯誤，也要創建 Item（如果強制創建）
                if force_create:
                    main_item = self.create_trade_item(main_item_data, city_code, city_name)
                    main_item['history_data'] = None  # 設為 None 表示無法獲取
                    main_item['trade_count'] = main_item_data.get('history_total', 1)
                    yield main_item
                return
            
            # 獲取歷史資料
            history_list = history_response.get('data', {}).get('history', [])
            
            self.logger.info(f"房屋 {house_id} 有 {len(history_list)} 筆歷史交易")
            
            # 創建主要 Item
            main_item = self.create_trade_item(main_item_data, city_code, city_name)
            
            if history_list:
                # 有歷史資料
                main_item['history_data'] = history_response.get('data', {})  # 保存完整歷史 JSON
                main_item['trade_count'] = len(history_list)  # 更新實際歷史交易數量
            else:
                # 沒有歷史資料，但 API 正常
                # 檢查 API 返回的資料結構，如果沒有歷史資料，設為 None
                history_data = history_response.get('data', {})
                if history_data and (history_data.get('history') or history_data.get('total') or len(history_data) > 1):
                    # 有其他有用的資料，保存
                    main_item['history_data'] = history_data
                else:
                    # 完全沒有有用的資料，設為 None
                    main_item['history_data'] = None
                main_item['trade_count'] = main_item_data.get('history_total', 1)
            
            yield main_item
                
        except json.JSONDecodeError as e:
            self.logger.error(f"解析房屋 {house_id} 歷史資料 JSON 失敗: {e}")
            # JSON 解析失敗，也要創建 Item（如果強制創建）
            if force_create:
                main_item = self.create_trade_item(main_item_data, city_code, city_name)
                main_item['history_data'] = None  # 設為 None 表示解析失敗
                main_item['trade_count'] = main_item_data.get('history_total', 1)
                yield main_item
        except Exception as e:
            self.logger.error(f"處理房屋 {house_id} 歷史資料時發生錯誤: {e}")
            # 其他錯誤，也要創建 Item（如果強制創建）
            if force_create:
                main_item = self.create_trade_item(main_item_data, city_code, city_name)
                main_item['history_data'] = None  # 設為 None 表示處理失敗
                main_item['trade_count'] = main_item_data.get('history_total', 1)
                yield main_item