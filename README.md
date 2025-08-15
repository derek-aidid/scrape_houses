# 🏠 Taiwan House Data Scraping System

A powerful Taiwan real estate data scraping system designed to collect house sales information and historical transaction data. This system supports multiple well-known real estate websites and provides comprehensive house information scraping, data processing, and database storage capabilities.

## ✨ Key Features

### 🏘️ House Sales Information Scrapers
- **Multi-Website Support**: Rakuya, Sinyi Real Estate, Yung Ching Real Estate, HouseFun, 5168 House Network
- **Complete House Information**: Price, area, layout, age, address, community information, etc.
- **Image Collection**: Automatic house photo downloads
- **Geolocation**: Longitude/latitude coordinates and address parsing
- **Real-time Updates**: Smart identification of new vs. existing houses to avoid duplicate scraping

### 📊 House Transaction History Scrapers
- **Rakuya Real Price Registration**: Historical transaction data for all 21 cities/counties in Taiwan
- **Detailed Transaction Info**: Transaction price, date, floor, area, etc.
- **Data Integration**: Unified field format supporting multi-source data merging
- **Batch Processing**: Efficient paginated scraping and data processing

### 🛠️ System Features
- **Proxy Support**: Built-in proxy server configuration to avoid IP blocking
- **Database Integration**: PostgreSQL database support with Azure export capabilities
- **Data Cleaning**: Automatic data formatting and validation
- **Error Handling**: Comprehensive error handling and logging
- **Scalable Architecture**: Modular design for easy addition of new scrapers

## 🚀 Quick Start

### System Requirements
- Python 3.7+
- PostgreSQL database (optional)
- Network connection and proxy server (recommended)

### Installation Steps

1. **Clone the Project**
```bash
git clone https://github.com/yourusername/scrape_houses.git
cd scrape_houses
```

2. **Install Dependencies**
```bash
pip install -r requirements.txt
```

3. **Configure Settings**
```bash
cd aidid_house
# Edit config.ini file to set database connection and proxy server
```

## 📁 Project Structure

```
scrape_houses/
├── aidid_house/                    # Main scraping project
│   ├── spiders/                    # Spider scripts
│   │   ├── buyRakuya.py          # Rakuya house scraper
│   │   ├── buyXinyi.py           # Sinyi Real Estate scraper
│   │   ├── buyYungChing.py       # Yung Ching Real Estate scraper
│   │   ├── buyHB.py              # HouseFun scraper
│   │   ├── buy5168.py            # 5168 House Network scraper
│   │   ├── rakuya_trades.py      # Rakuya transaction history scraper
│   │   └── ...                   # Other spider scripts
│   ├── items.py                   # Data item definitions
│   ├── pipelines.py               # Data processing pipelines
│   ├── middlewares.py             # Middleware
│   ├── settings.py                # Scraper settings
│   ├── config.ini                 # Configuration file
│   └── postgres2Azure.py          # Database export tool
├── requirements.txt                # Python dependencies
└── scrapy.cfg                     # Scrapy configuration file
```

## 🕷️ Scraper Usage Guide

### House Sales Information Scrapers

#### Rakuya Scraper
```bash
cd aidid_house
scrapy crawl buyRakuya
```

**Features:**
- Scrapes house sales information from all 21 cities/counties in Taiwan
- Automatically parses detailed house information and images
- Supports JavaScript-rendered pages
- Smart deduplication and update mechanisms

#### Sinyi Real Estate Scraper
```bash
scrapy crawl buyXinyi
```

**Features:**
- Scrapes Sinyi Real Estate sales listings
- Complete house information collection
- Address and geolocation parsing

#### Yung Ching Real Estate Scraper
```bash
scrapy crawl buyYungChing
```

**Features:**
- Yung Ching Real Estate sales data scraping
- Community information and house features
- Price and area data

### House Transaction History Scrapers

#### Rakuya Real Price Registration Scraper
```bash
scrapy crawl rakuya_trades
```

**Features:**
- Historical transaction data for all 21 cities/counties in Taiwan
- Supports paginated batch scraping
- Unified data format output
- Detailed transaction information collection

## 📊 Data Structure

### House Sales Information (AididHouseItem)
```python
{
    'url': 'House page URL',
    'site': 'Source website',
    'name': 'House name',
    'address': 'Complete address',
    'longitude': 'Longitude',
    'latitude': 'Latitude',
    'city': 'City',
    'district': 'District',
    'price': 'Price',
    'space': 'Area',
    'layout': 'Layout',
    'age': 'House age',
    'floors': 'Floor level',
    'community': 'Community name',
    'basic_info': 'Basic information',
    'features': 'Features',
    'life_info': 'Life amenities',
    'utility_info': 'Public facilities',
    'trade_data': 'Transaction data',
    'review': 'Reviews',
    'images': 'House images',
    'house_id': 'House ID'
}
```

### House Transaction History (RakuyaTradeItem)
```python
{
    'url': 'Transaction detail page URL',
    'house_id': 'Unified house ID',
    'city_name': 'City name',
    'area_name': 'Area name',
    'address': 'Address',
    'community_name': 'Community name',
    'total_area': 'Total area in ping',
    'price_per_ping': 'Price per ping',
    'total_price': 'Total price',
    'close_date': 'Transaction date',
    'building_age': 'Building age',
    'floor_info': 'Floor information',
    'bedrooms': 'Number of bedrooms',
    'livingrooms': 'Number of living rooms',
    'bathrooms': 'Number of bathrooms',
    'layout': 'Layout description'
}
```

## ⚙️ Configuration

### config.ini Settings
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

### Proxy Server Configuration
The system supports various proxy server configurations:
- HTTP/HTTPS proxies
- Authenticated proxies
- Rotating proxies
- Automatic proxy selection

## 🗄️ Database Integration

### PostgreSQL Support
- Automatic table creation
- Data type validation
- Index optimization
- Batch insertion

### Azure Export
```bash
python postgres2Azure.py
```

**Features:**
- Database data export
- CSV format support
- Automatic data cleaning
- Batch processing

## 🔧 Advanced Features

### Custom Scrapers
1. Create new spider files in the `spiders/` directory
2. Inherit from `scrapy.Spider` class
3. Implement necessary parsing methods
4. Register spiders in `settings.py`

### Data Processing Pipelines
- Automatic data cleaning and formatting
- Duplicate data detection
- Data validation and error handling
- Custom output formats

### Middleware Functions
- Proxy server management
- Request retry mechanisms
- User agent rotation
- Request frequency control

## 📈 Performance Optimization

### Scraping Speed Optimization
- Concurrent request control
- Intelligent delay settings
- Proxy server rotation
- Memory usage optimization

### Data Processing Optimization
- Batch database operations
- Asynchronous processing
- Data compression
- Caching mechanisms

## 🚨 Important Notes

### Legal and Ethical Considerations
- Please respect the robots.txt rules of target websites
- Reasonably control scraping frequency to avoid burdening servers
- Use only for learning and research purposes
- Comply with relevant laws and regulations

### Technical Considerations
- Regularly update proxy server settings
- Monitor scraping logs and errors
- Backup important data
- Regularly check for changes in target website structures

## 🐛 Troubleshooting

### Common Issues

**Q: Scraper won't start?**
A: Check Python version, dependency installation, and configuration file settings

**Q: Data scraping fails?**
A: Check network connection, proxy server settings, and target website status

**Q: Database connection errors?**
A: Confirm database service status and connection parameters

**Q: Proxy server not working?**
A: Check proxy server availability and authentication information

### Logging and Debugging
- Enable detailed logging
- Use Scrapy's built-in debugging tools
- Check network requests and responses
- Monitor memory and CPU usage

## 🤝 Contributing

We welcome community contributions! Please follow these steps:

1. Fork the project
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

### Contribution Types
- 🐛 Bug fixes
- ✨ New feature development
- 📚 Documentation improvements
- 🧪 Test cases
- 🔧 Performance optimization

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details

## 📞 Contact Information

- Project Maintainer: [Your Name]
- Email: [your.email@example.com]
- Project URL: [https://github.com/yourusername/scrape_houses]
- Issue Reports: [https://github.com/yourusername/scrape_houses/issues]

## 🙏 Acknowledgments

Thanks to the following open source projects and tools:
- [Scrapy](https://scrapy.org/) - Powerful Python scraping framework
- [PostgreSQL](https://www.postgresql.org/) - Reliable relational database
- [Python](https://www.python.org/) - Excellent programming language

---

**⚠️ Disclaimer**: This tool is for learning and research purposes only. Users should comply with relevant laws and regulations and website terms of use, and bear all risks and responsibilities for using this tool.
