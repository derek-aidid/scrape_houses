# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class AididHouseItem(scrapy.Item):
    # define the fields for your item here like:
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
