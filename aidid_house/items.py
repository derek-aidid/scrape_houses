import scrapy

class AididHouseItem(scrapy.Item):
    # This is the full item for a house listing, matching your original schema.
    url = scrapy.Field()
    site = scrapy.Field()
    name = scrapy.Field()
    address = scrapy.Field()
    longitude = scrapy.Field()
    latitude = scrapy.Field()
    city = scrapy.Field()
    district = scrapy.Field()
    price = scrapy.Field()
    space = scrapy.Field()
    layout = scrapy.Field()
    age = scrapy.Field()
    floors = scrapy.Field()
    community = scrapy.Field()
    basic_info = scrapy.Field()
    features = scrapy.Field()
    life_info = scrapy.Field()
    utility_info = scrapy.Field()
    trade_data = scrapy.Field()
    review = scrapy.Field()
    images = scrapy.Field()
    house_id = scrapy.Field()

class HouseUpdateItem(scrapy.Item):
    # This is a lightweight item used only to update the 'last_seen'
    # timestamp for an existing house URL.
    url = scrapy.Field()

class SalesmanItem(scrapy.Item):
    # This item is currently not used but kept for potential future use.
    site = scrapy.Field()
    salesman = scrapy.Field()
    link = scrapy.Field()
    brand_name = scrapy.Field()
    store_name = scrapy.Field()
    legal_company_name = scrapy.Field()
    phone = scrapy.Field()
    profile_image_url = scrapy.Field()
    property_url = scrapy.Field()

class RakuyaTradeItem(scrapy.Item):
    # Item for Rakuya historical trade data with master table support
    # 支援統一欄位合併和歷史交易功能
    
    # === 基本識別欄位 ===
    url = scrapy.Field()                    # 交易詳情頁面 URL (pipeline 需要)
    case_url = scrapy.Field()               # 案件詳情頁面 URL
    house_id = scrapy.Field()               # 統一房屋 ID (dealId/sn)
    city_code = scrapy.Field()              # 城市代碼 (0-20)
    city_name = scrapy.Field()              # 城市名稱
    area_name = scrapy.Field()              # 區域名稱 (統一 zipcodeArea/areaName)
    zipcode = scrapy.Field()                # 郵遞區號
    
    # === 地址和社區資訊 ===
    address = scrapy.Field()                # 統一地址 (addr/address/addrBuNo)
    community_name = scrapy.Field()         # 統一社區名稱 (community/communityName)
    community_id = scrapy.Field()           # 社區 ID
    community_url = scrapy.Field()          # 社區頁面 URL
    
    # === 房屋基本資訊 ===
    property_type = scrapy.Field()          # 物件類型 (純車位、住宅等)
    sell_type_code = scrapy.Field()         # 銷售類型代碼
    sell_type_code_short = scrapy.Field()   # 銷售類型簡稱
    
    # === 價格和面積資訊 ===
    total_area = scrapy.Field()             # 統一總坪數 (totalSize)
    price_per_ping = scrapy.Field()         # 每坪價格 (萬/坪)
    total_price = scrapy.Field()            # 總價 (萬)
    garage_size = scrapy.Field()            # 車位面積
    garage_price = scrapy.Field()           # 車位價格
    
    # === 建築資訊 ===
    building_age = scrapy.Field()           # 屋齡
    build_date = scrapy.Field()             # 建築日期
    floor_info = scrapy.Field()             # 樓層資訊 (1/15樓)
    trans_floor = scrapy.Field()            # 統一交易樓層 (transFloor/transFloors)
    sur_floor = scrapy.Field()              # 統一建築總樓層 (surFloor/surFloors)
    building_floor = scrapy.Field()         # 統一建築樓層描述 (buildingFloor/buildingFloors)
    has_elevator = scrapy.Field()           # 是否有電梯
    
    # === 房間配置 ===
    bedrooms = scrapy.Field()               # 房間數
    livingrooms = scrapy.Field()            # 客廳數
    bathrooms = scrapy.Field()              # 浴室數
    layout = scrapy.Field()                 # 格局描述
    
    # === 面積詳細資訊 ===
    main_size = scrapy.Field()              # 主建物面積
    sub_size = scrapy.Field()               # 附屬建物面積
    balcony_size = scrapy.Field()           # 陽台面積
    share_size = scrapy.Field()             # 共有面積
    base_size = scrapy.Field()              # 基地面積
    build_size = scrapy.Field()             # 建物面積
    
    # === 交易資訊 ===
    close_date = scrapy.Field()             # 成交日期
    trade_count = scrapy.Field()            # 統一歷史交易次數 (historyTotal/snGrountCnt)
    pay_type = scrapy.Field()               # 付款類型
    memo = scrapy.Field()                   # 備註
    contract_memo = scrapy.Field()          # 合約備註
    
    # === 歷史交易支援 ===
    is_historical = scrapy.Field()          # 是否為歷史交易資料
    original_house_id = scrapy.Field()      # 原始房屋 ID (歷史交易用)
    history_sequence = scrapy.Field()       # 歷史交易序號
    history_data = scrapy.Field()           # 原始歷史資料 (JSON)
    
    # === 狀態標記 ===
    is_special = scrapy.Field()             # 是否為特殊交易
    is_presale = scrapy.Field()             # 是否為預售
    is_on_sale = scrapy.Field()             # 是否正在銷售
    include_garage = scrapy.Field()         # 是否包含車位
    has_garage = scrapy.Field()             # 是否有車位
    
    # === 完整資料保存 ===
    basic_info = scrapy.Field()             # 其他基本資訊 (JSON)
    trade_data = scrapy.Field()             # 交易資料 (JSON)
    original_data = scrapy.Field()          # 完整原始資料 (JSON)
    
    # === 系統欄位 ===
    scraped_at = scrapy.Field()             # 爬取時間戳記
    last_seen = scrapy.Field()              # 最後見到時間
    data_status = scrapy.Field()            # 資料狀態 (ACTIVE/INACTIVE/DELISTED)
