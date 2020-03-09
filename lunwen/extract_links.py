import logging
import pymysql as pq

from scrapy.loader import Selector


class SelfLinkExtractor:

    def __init__(self, response):
        if response is None or response.body is None:
            raise 'response or response.body is None {}'.format(response)
        self.response = response
        self.selector = Selector(self.response)
        self.conn = pq.connect(host='134.175.16.232',
                               user='sunzeyu',
                               password='2168',
                               database='lunwen')

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

    def _compare_with_database(self, data):
        name, url = data
        try:
            self.conn.ping()
            logging.info('\t数据库活跃:链接提取\t')
        except Exception as e:
            logging.info('\t数据库失去连接{},准备重新连接:链接提取\t'.format(e))
            self.conn = pq.connect(host='134.175.16.232',
                                   user='sunzeyu',
                                   password='2168',
                                   database='lunwen')
        try:
            with self.conn.cursor() as cursor:
                sql = """
                    select name from roomInfo where name = '%s';
                """
                res = cursor.execute(
                    sql % name
                )
        except Exception as e:
            logging.info('\t链接提取：URL-->查询出现错误 {}\n\t'.format(e))
        if not res:
            return url
        logging.info('\t链接提取：匹配到数据')
        return None

    def extract_url(self):
        count = 0
        urls = list()
        for data in self._get_url_info():
            count += 1
            url = self._compare_with_database(data)
            if url:
                urls.append(url)
        logging.info('\t共匹配到--{}--个URL'.format(count))
        return urls