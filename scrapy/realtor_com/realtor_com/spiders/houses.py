# -*- coding: utf-8 -*-
import scrapy
import pandas as pd
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor


class HousesSpider(scrapy.Spider):
    name = 'houses'
    
    def __init__(self, zipcodes, *args, **kwargs):
    	super(MySpider, self).__init__(*args, **kwargs)
    	zipcode_table = pd.read_csv(zipcodes = pd.read_csv(args.zipcode, dtype={"zipcode": object}))
    	zipcodes = zipcodes_table.zipcode.values.tolist()
    	self.allowed_domains = ['realtor.com']
    	self.start_urls = ['http://realtor.com/realestateandhomes-search/{}'.format(zipcode) for zipcode in zipcodes]

    def parse(self, response):
        pass
