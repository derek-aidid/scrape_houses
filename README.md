# 🏠 台灣房屋資料爬蟲系統

一個強大的台灣房地產資料爬蟲系統，專門用於收集房屋銷售資訊和歷史交易資料。本系統支援多個知名房地產網站，提供完整的房屋資訊爬取、資料處理和資料庫儲存功能。

## ✨ 主要功能特色

### 🏘️ 房屋銷售資訊爬蟲
- **多網站支援**: 樂屋網、信義房屋、永慶房屋、好房網、5168 房屋網
- **完整房屋資訊**: 價格、面積、格局、屋齡、地址、社區資訊等
- **圖片收集**: 自動下載房屋照片
- **地理位置**: 經緯度座標和地址解析
- **即時更新**: 智能識別新舊房屋，避免重複爬取

### 📊 房屋交易歷史爬蟲
- **樂屋網實價登錄**: 全台 21 個縣市的歷史交易資料
- **詳細交易資訊**: 成交價格、日期、樓層、面積等
- **資料整合**: 統一欄位格式，支援多來源資料合併
- **批量處理**: 高效的分頁爬取和資料處理

### 🛠️ 系統功能
- **代理支援**: 內建代理伺服器配置，避免 IP 封鎖
- **資料庫整合**: PostgreSQL 資料庫支援，可匯出至 Azure
- **資料清理**: 自動資料格式化和驗證
- **錯誤處理**: 完善的錯誤處理和日誌記錄
- **可擴展架構**: 模組化設計，易於添加新的爬蟲

## 🚀 快速開始

### 系統需求
- Python 3.7+
- PostgreSQL 資料庫 (可選)
- 網路連線和代理伺服器 (建議)

### 安裝步驟

1. **克隆專案**
```bash
git clone https://github.com/yourusername/scrape_houses.git
cd scrape_houses
```

2. **安裝依賴套件**
```bash
pip install -r requirements.txt
```

3. **配置設定檔**
```bash
cd aidid_house
# 編輯 config.ini 檔案，設定資料庫連線和代理伺服器
```

## 📁 專案結構

```
scrape_houses/
├── aidid_house/                    # 主要爬蟲專案
│   ├── spiders/                    # 爬蟲腳本
│   │   ├── buyRakuya.py          # 樂屋網房屋爬蟲
│   │   ├── buyXinyi.py           # 信義房屋爬蟲
│   │   ├── buyYungChing.py       # 永慶房屋爬蟲
│   │   ├── buyHB.py              # 好房網爬蟲
│   │   ├── buy5168.py            # 5168 房屋網爬蟲
│   │   ├── rakuya_trades.py      # 樂屋網交易歷史爬蟲
│   │   └── ...                   # 其他爬蟲腳本
│   ├── items.py                   # 資料項目定義
│   ├── pipelines.py               # 資料處理管道
│   ├── middlewares.py             # 中間件
│   ├── settings.py                # 爬蟲設定
│   ├── config.ini                 # 配置檔案
│   └── postgres2Azure.py          # 資料庫匯出工具
├── requirements.txt                # Python 依賴套件
└── scrapy.cfg                     # Scrapy 配置檔案
```

## 🕷️ 爬蟲使用說明

### 房屋銷售資訊爬蟲

#### 樂屋網爬蟲
```bash
cd aidid_house
scrapy crawl buyRakuya
```

**功能特色:**
- 爬取全台 21 個縣市的房屋銷售資訊
- 自動解析房屋詳細資訊和圖片
- 支援 JavaScript 渲染頁面
- 智能去重和更新機制

#### 信義房屋爬蟲
```bash
scrapy crawl buyXinyi
```

**功能特色:**
- 爬取信義房屋銷售物件
- 完整房屋資訊收集
- 地址和地理位置解析

#### 永慶房屋爬蟲
```bash
scrapy crawl buyYungChing
```

**功能特色:**
- 永慶房屋銷售資料爬取
- 社區資訊和房屋特色
- 價格和面積資料

### 房屋交易歷史爬蟲

#### 樂屋網實價登錄爬蟲
```bash
scrapy crawl rakuya_trades
```

**功能特色:**
- 全台 21 個縣市歷史交易資料
- 支援分頁批量爬取
- 統一資料格式輸出
- 詳細的交易資訊收集

## 📊 資料結構

### 房屋銷售資訊 (AididHouseItem)
```python
{
    'url': '房屋頁面網址',
    'site': '來源網站',
    'name': '房屋名稱',
    'address': '完整地址',
    'longitude': '經度',
    'latitude': '緯度',
    'city': '城市',
    'district': '區域',
    'price': '價格',
    'space': '面積',
    'layout': '格局',
    'age': '屋齡',
    'floors': '樓層',
    'community': '社區名稱',
    'basic_info': '基本資訊',
    'features': '特色',
    'life_info': '生活機能',
    'utility_info': '公共設施',
    'trade_data': '交易資料',
    'review': '評價',
    'images': '房屋圖片',
    'house_id': '房屋 ID'
}
```

### 房屋交易歷史 (RakuyaTradeItem)
```python
{
    'url': '交易詳情頁面網址',
    'house_id': '統一房屋 ID',
    'city_name': '城市名稱',
    'area_name': '區域名稱',
    'address': '地址',
    'community_name': '社區名稱',
    'total_area': '總坪數',
    'price_per_ping': '每坪價格',
    'total_price': '總價',
    'close_date': '成交日期',
    'building_age': '屋齡',
    'floor_info': '樓層資訊',
    'bedrooms': '房間數',
    'livingrooms': '客廳數',
    'bathrooms': '浴室數',
    'layout': '格局描述'
}
```

## ⚙️ 配置說明

### config.ini 設定
```ini
[database]
host = localhost
port = 5432
database = your_database
user = your_username
password = your_password

[proxy]
enabled = true
proxy_url = http://your_proxy:port
username = your_proxy_username
password = your_proxy_password

[scraping]
delay = 1
concurrent_requests = 16
download_timeout = 30
```

### 代理伺服器設定
系統支援多種代理伺服器配置：
- HTTP/HTTPS 代理
- 認證代理
- 輪換代理
- 自動代理選擇

## 🗄️ 資料庫整合

### PostgreSQL 支援
- 自動建立資料表
- 資料類型驗證
- 索引優化
- 批量插入

### Azure 匯出
```bash
python postgres2Azure.py
```

**功能:**
- 資料庫資料匯出
- CSV 格式支援
- 自動資料清理
- 批次處理

## 🔧 進階功能

### 自定義爬蟲
1. 在 `spiders/` 目錄下建立新的爬蟲檔案
2. 繼承 `scrapy.Spider` 類別
3. 實作必要的解析方法
4. 在 `settings.py` 中註冊爬蟲

### 資料處理管道
- 自動資料清理和格式化
- 重複資料檢測
- 資料驗證和錯誤處理
- 自定義輸出格式

### 中間件功能
- 代理伺服器管理
- 請求重試機制
- 用戶代理輪換
- 請求頻率控制

## 📈 效能優化

### 爬取速度優化
- 並發請求控制
- 智能延遲設定
- 代理伺服器輪換
- 記憶體使用優化

### 資料處理優化
- 批量資料庫操作
- 非同步處理
- 資料壓縮
- 快取機制

## 🚨 注意事項

### 法律和道德考量
- 請遵守目標網站的 robots.txt 規則
- 合理控制爬取頻率，避免對伺服器造成負擔
- 僅用於學習和研究目的
- 遵守相關法律法規

### 技術注意事項
- 定期更新代理伺服器設定
- 監控爬取日誌和錯誤
- 備份重要資料
- 定期檢查目標網站結構變化

## 🐛 疑難排解

### 常見問題

**Q: 爬蟲無法啟動？**
A: 檢查 Python 版本、依賴套件安裝和設定檔配置

**Q: 資料爬取失敗？**
A: 檢查網路連線、代理伺服器設定和目標網站狀態

**Q: 資料庫連線錯誤？**
A: 確認資料庫服務狀態和連線參數

**Q: 代理伺服器無效？**
A: 檢查代理伺服器可用性和認證資訊

### 日誌和除錯
- 啟用詳細日誌記錄
- 使用 Scrapy 內建除錯工具
- 檢查網路請求和回應
- 監控記憶體和 CPU 使用

## 🤝 貢獻指南

我們歡迎社群貢獻！請遵循以下步驟：

1. Fork 專案
2. 建立功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交變更 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 開啟 Pull Request

### 貢獻類型
- 🐛 Bug 修復
- ✨ 新功能開發
- 📚 文檔改進
- 🧪 測試案例
- 🔧 效能優化

## 📄 授權條款

本專案採用 MIT 授權條款 - 詳見 [LICENSE](LICENSE) 檔案

## 📞 聯絡資訊

- 專案維護者: [Your Name]
- 電子郵件: [your.email@example.com]
- 專案網址: [https://github.com/yourusername/scrape_houses]
- 問題回報: [https://github.com/yourusername/scrape_houses/issues]

## 🙏 致謝

感謝以下開源專案和工具：
- [Scrapy](https://scrapy.org/) - 強大的 Python 爬蟲框架
- [PostgreSQL](https://www.postgresql.org/) - 可靠的關聯式資料庫
- [Python](https://www.python.org/) - 優秀的程式語言

---

**⚠️ 免責聲明**: 本工具僅供學習和研究使用。使用者應遵守相關法律法規和網站使用條款，並承擔使用本工具的所有風險和責任。
