# -*- coding: utf-8 -*-

import scrapy

class ActiveForeignPrincipalItem(scrapy.Item):
    url = scrapy.Field(default="")
    country = scrapy.Field(default="")
    state = scrapy.Field(default=None)
    reg_num = scrapy.Field(default="")
    address = scrapy.Field(default="")
    foreign_principal = scrapy.Field(default="")
    date = scrapy.Field(serializer=str)
    registrant = scrapy.Field(default="")
    exhibit_url = scrapy.Field(default="")


