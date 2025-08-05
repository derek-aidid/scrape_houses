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
