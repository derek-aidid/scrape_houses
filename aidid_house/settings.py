# Scrapy settings for aidid_house project

BOT_NAME = "aidid_house"
LOG_STDOUT = False

# --- ScrapeOps Settings ---
SCRAPEOPS_API_KEY = '4a151e78-1817-48b6-b496-ec2297a76592'
SCRAPEOPS_FAKE_USER_AGENT_ENDPOINT = 'https://headers.scrapeops.io/v1/user-agents'
SCRAPEOPS_FAKE_USER_AGENT_ENABLED = True
SCRAPEOPS_NUM_RESULTS = 10000

SPIDER_MODULES = ["aidid_house.spiders"]
NEWSPIDER_MODULE = "aidid_house.spiders"

ROBOTSTXT_OBEY = False

# --- Middleware Settings ---
SPIDER_MIDDLEWARES = {
   "aidid_house.middlewares.AididHouseSpiderMiddleware": 543,
}

DOWNLOADER_MIDDLEWARES = {
   'aidid_house.middlewares.ScrapeOpsFakeBrowserHeaderAgentMiddleware': 400,
   'scrapeops_scrapy.middleware.retry.RetryMiddleware': 550,
   'scrapy.downloadermiddlewares.retry.RetryMiddleware': None,
}

# --- Extension Settings ---
EXTENSIONS = {
   'scrapeops_scrapy.extension.ScrapeOpsMonitor': 500,
}

# --- Pipeline Settings (Updated for New Architecture) ---
# The order is important:
# 1. AididHousePipeline cleans the data.
# 2. DeltaScrapePipeline handles all database logic (filtering, saving, updating).
ITEM_PIPELINES = {
   "aidid_house.pipelines.AididHousePipeline": 100,
   "aidid_house.pipelines.DeltaScrapePipeline": 200,
}

DOWNLOAD_FAIL_ON_DATALOSS = False

# --- Scrapy Core Settings ---
REQUEST_FINGERPRINTER_IMPLEMENTATION = "2.7"
TWISTED_REACTOR = "twisted.internet.asyncioreactor.AsyncioSelectorReactor"
FEED_EXPORT_ENCODING = "utf-8"