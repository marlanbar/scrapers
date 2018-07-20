# -*- coding: utf-8 -*-
import scrapy



class RealtorsSpider(scrapy.Spider):
    name = 'realtors'


    def __init__(self, zipcodes=[], **kwargs):
    	self.start_urls = []


    def parse(self, response):
        pass
