import unittest

from apexscraper.spiders import simple as simple_spider
from apexscraper.items import ActiveForeignPrincipalItem

from tests.utils import fake_response_from_file


class SimpleAFPSpiderTest(unittest.TestCase):
    def setUp(self):
        class TestableSimpleAFPSpider(simple_spider.SimpleAFPSpider):
            start_urls = ["file:///./tests/data/afp.csv"]

        self.spider = TestableSimpleAFPSpider()

    def test_parse_details(self):
        response = fake_response_from_file('data/parse_details.csv')
        item = ActiveForeignPrincipalItem()
        item['exhibit_url'] = ""
        response.meta['item'] = item
        results = self.spider.parse_details(response)
        self.assertEqual(item['exhibit_url'], "http://www.fara.gov/docs/3690-Exhibit-AB-20160614-10.pdf")

