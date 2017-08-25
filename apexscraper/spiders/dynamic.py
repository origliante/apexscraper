import future
from future.standard_library import install_aliases
from future.moves.urllib.parse import urljoin

import datetime
import scrapy
from scrapy import Selector
from scrapy.http.request import Request
from scrapy.spiders import CSVFeedSpider, Spider
from scrapy.utils.iterators import csviter


#APEX 4.2
#http://apextips.blogspot.it/2012/09/apex-ajax-basics.html

URL_PREFIX = "https://efile.fara.gov/pls/apex/"


class FaraCSVFeedSpider(CSVFeedSpider):
    name = "fara_csv"
    allowed_domains = ["www.fara.gov", "efile.fara.gov"]
    start_urls = [""] # special handling, see start_request()
    delimiter = ','
    quotechar = '"'
    fara_section = None

    def start_requests(self):
        start_url = "https://www.fara.gov/quick-search.html"
        yield Request(url=start_url, callback=self.get_apex_url)

    def get_apex_url(self, r):
        apex_url = self.extract_url(r, "//iframe/@src")
        yield Request(url=apex_url, callback=self.get_section_url)

    def get_section_url(self, r):
        section_url = self.extract_url(r,
            '//font[normalize-space(text())="{}"]/parent::a/@href'.format(self.fara_section))
        yield Request(url=section_url, callback=self.get_csv_url)

    def get_csv_url(self, r):
        p_instance = self.get_value_of('pInstance', r)
        p_flow_id = self.get_value_of('pFlowId', r)
        p_flow_step_id = self.get_value_of('pFlowStepId', r)
        url_args = "f?p={}:{}:{}:CSV::::".format(p_flow_id, p_flow_step_id, p_instance)
        csv_url = urljoin(URL_PREFIX, url_args)
        yield Request(url=csv_url, callback=self.parse)

    def get_value_of(self, element_id, response):
        return response.xpath("//*[@id='{}']/@value".format(element_id)).extract_first()

    def extract_url(self, r, xpq):
        extracted = r.xpath(xpq).extract()
        if not extracted or len(extracted) != 1:
            msg = 'URL not found. Page structure of "{}" probably changed!'.format(r.url)
            self.logger.critical(msg)
            raise scrapy.exceptions.CloseSpider(msg)
        url = extracted[0].strip()
        if url[0:4] != 'http':
            url = urljoin(URL_PREFIX, url)
        return url


class AFPSpider(FaraCSVFeedSpider):
    name = 'afpspider'
    fara_section = "Active Foreign Principals"

    def parse_row(self, response, row):
        return row

class ARSpider(FaraCSVFeedSpider):
    name = 'arspider'
    fara_section = "Active Registrants in a Date Range"

    def parse_row(self, response, row):
        return row


