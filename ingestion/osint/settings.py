BOT_NAME = "osint"

SPIDER_MODULES = ["osint.spiders"]
NEWSPIDER_MODULE = "osint.spiders"

ROBOTSTXT_OBEY = True

DOWNLOAD_DELAY = 1.5
AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_START_DELAY = 1.0
AUTOTHROTTLE_MAX_DELAY = 10.0
CONCURRENT_REQUESTS = 4

DEFAULT_REQUEST_HEADERS = {
    'User-Agent': 'OSINT-Research-Bot/0.1 (+contact: research@example.org)'
}

ITEM_PIPELINES = {
    "osint.pipelines.PostgresPipeline": 300,
}

LOG_LEVEL = "INFO"
