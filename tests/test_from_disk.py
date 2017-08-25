import unittest

import json
import os
import logging

import scrapy
from scrapy.crawler import CrawlerProcess

from apexscraper.spiders import simple as simple_spider
from apexscraper.items import ActiveForeignPrincipalItem


simple_spider.FARA_URL_PREFIX = "file://{}/tests/data/".format(os.getcwd())
 
class TestableSimpleAFPSpider(simple_spider.SimpleAFPSpider):
    start_urls = ["file://{}/tests/data/afp.csv".format(os.getcwd()) ]


TEST_RESULT_FILE = './tests/results/json_result.json'
TEST_CONTROL_FILE = './tests/control/json_control.json'


class SimpleAFPSpiderTest(unittest.TestCase):
    def setUp(self):
        self.process = CrawlerProcess({
            'FEED_FORMAT': 'jsonlines',
            'FEED_URI': TEST_RESULT_FILE
        })

        # disabled log under CRITICAL
        logging.disable(logging.CRITICAL)

        os.remove(TEST_RESULT_FILE)

        self.process.crawl(TestableSimpleAFPSpider)
        # will block here until the crawling is finished
        self.process.start()

    def test_json(self):
        controls = []
        results = []

        with open(TEST_RESULT_FILE, 'r') as f:
            for line in f:
                results.append(json.loads(line))

        with open(TEST_CONTROL_FILE, 'r') as f:
            for line in f:
                controls.append(json.loads(line))

        # in test data files reg_num are unique
        for c in controls:
            for r in results:
                if c['reg_num'] == r['reg_num']:
                    #TODO: also handle url
                    c.pop('url')
                    r.pop('url')
                    self.assertEqual(c, r)
                    break


