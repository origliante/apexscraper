import future
from future.standard_library import install_aliases
from future.moves.urllib.parse import urljoin

import re
import datetime
import tidylib

import scrapy
from scrapy.http.request import Request
from scrapy.spiders import CSVFeedSpider
from scrapy.utils.iterators import csviter

from apexscraper.settings import FARA_URL_PREFIX, FARA_DOMAINS, AFP_START_URL
from apexscraper.items import ActiveForeignPrincipalItem


class SimpleAFPSpider(CSVFeedSpider):
    name = "afp_simple"
    allowed_domains = FARA_DOMAINS
    start_urls = [AFP_START_URL]
    delimiter = ','
    quotechar = '"'
    afp_header = ["Country/LocationRepresented","Foreign Principal","Foreign PrincipalRegistration Date","Address","State","Registrant","Registration #","RegistrationDate"]
    afp_details_header = ["Date Stamped","View Document","Registration #","Registrant Name","Document Type"]

    def check_header(self, A, B):
        for k in A:
            if k not in B:
                msg = "CSV header differs! A: [{}] - B: [{}]".format(A, B)
                raise scrapy.exceptions.CloseSpider(msg)

    def _get_value(self, row, k):
        """
            Basic row value handling.
        """
        v = row[k]
        if k == 'Address':
            if not v: return None
            #TODO: think about better address normalization
            v = v.replace('&nbsp;', ' ').replace('<br>', ' ')
            v = v.strip()
            return v
        elif k == 'State':
            if not v: return None
            return v
        elif k == 'Foreign PrincipalRegistration Date':
            if not v: return None
            try:
                rv = datetime.datetime.strptime(v, "%m/%d/%Y").date()
                return rv
            except ValueError:
                #TODO: raise scrapy.exceptions.CloseSpider?
                return None
        return v

    def parse_row(self, response, row):
        item = ActiveForeignPrincipalItem()

        #FIXME: check_header runs at every row...
        #I do this because
        # 1) scrapy iterator considers the first line as a regular line if you specify the header
        # 2) if the header is different, we have to stop for consistency 
        #
        # we could add a layer that passes lines through cutplace
        # to validate every field on a ruleset
        # https://pypi.python.org/pypi/cutplace/
        self.check_header(row.keys(), self.afp_header)

        item['country'] = self._get_value(row, 'Country/LocationRepresented')
        item['state'] = self._get_value(row, 'State')
        item['reg_num'] = self._get_value(row, 'Registration #')
        item['address'] = self._get_value(row, 'Address')
        item['foreign_principal'] = self._get_value(row, 'Foreign Principal')
        item['date'] = self._get_value(row, 'Foreign PrincipalRegistration Date')
        item['registrant'] = self._get_value(row, 'Registrant')
        item['exhibit_url'] = None
        item['url'] = None

        # the detail url
        url_args = "f?p=171:200:0::NO:RP,200:P200_REG_NUMBER,P200_DOC_TYPE,P200_COUNTRY:{},Exhibit%20AB,{}".format(
            item['reg_num'] if item['reg_num'] else "",
            item['country'] if item['country'] else ""
        )
        item['url'] = urljoin(FARA_URL_PREFIX, url_args)

        # csv detail url
        url_args = "f?p=171:200:0:CSV:NO:RP,200:P200_REG_NUMBER,P200_DOC_TYPE,P200_COUNTRY:{},Exhibit%20AB,{}".format(
            item['reg_num'] if item['reg_num'] else "",
            item['country'] if item['country'] else ""
        )
        csv_detail_url = urljoin(FARA_URL_PREFIX, url_args)
        request = Request(url=csv_detail_url, callback=self.parse_details, errback=self.return_item_if_errback, dont_filter=True)
        request.meta['item'] = item
        yield request

    def return_item_if_errback(self, response):
        """
        This is called in case of errors on the detail_url above.
        """
        return response.request.meta['item']

    def parse_details(self, response):
        """
        Called one time for each Active Foreign Principal.
        """
        most_recent = None

        for row in csviter(response, self.delimiter, []):
            #FIXME: check_header at every row...
            self.check_header(row.keys(), self.afp_details_header)
            row['date'] = datetime.datetime.strptime(row['Date Stamped'], "%m/%d/%Y").date()
            if not most_recent:
                most_recent = row
            elif row['date'] > most_recent['date']:
                most_recent = row

        item = response.meta['item']
        if most_recent:
            # html markup sanitize
            doc, errs = tidylib.tidy_document(most_recent['View Document'])
            urls = re.findall('http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+',
                doc)
            #TODO: should handle case with urls > 1? --> log WARNING?
            if urls:
                item['exhibit_url'] = urls[0]
        return item


