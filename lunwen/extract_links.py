import logging
import pymysql as pq


from .database import self_mysql
from scrapy.loader import Selector


class SelfLinkExtractor:

    def __init__(self, response):
        if response is None or response.body is None:
            raise 'response or response.body is None {}'.format(response)
        self.response = response
        self.selector = Selector(self.response)

    def _get_url_info(self):
        name = None
        url = None
        try:
            name = self.selector.xpath('//h3//b/text()').getall()
            url = self.selector.xpath('//h3/a/@href').getall()
        except Exception as e:
            logging.info('\t获取失败 {}'.format(e))
        name_url = zip(name, url)
        logging.info('\t{}\t获取的链接数据有：{}'.format(self.response.request.url, name_url))
        return name_url

    @staticmethod
    def _compare_with_database(data):
        name, url = data
        sql = """
            select name from roomInfo where name = '%s';
        """
        res = self_mysql.exec(
            sql % name
        )
        if not res:
            logging.info('\t链接提取--未能匹配到数据--YES')
            return url
        logging.info('\t链接提取--匹配到数--NO')
        return None

    def extract_url(self):
        count = 0
        urls = list()
        for data in self._get_url_info():
            url = self._compare_with_database(data)
            if url:
                count += 1
                urls.append(url)
        logging.info('\t共匹配到--{}--个URL'.format(count))
        return urls
