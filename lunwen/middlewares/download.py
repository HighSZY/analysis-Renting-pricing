import logging
import random
import re
import time

import requests
from scrapy.downloadermiddlewares.useragent import UserAgentMiddleware
from scrapy.downloadermiddlewares.redirect import RedirectMiddleware
from scrapy.http import TextResponse
from six.moves.urllib.parse import urljoin
from w3lib.url import safe_url_string

from ..database import self_redis, redis_key

user_agent_list = [
    "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.1 "
    "(KHTML, like Gecko) Chrome/22.0.1207.1 Safari/537.1",
    "Mozilla/5.0 (X11; CrOS i686 2268.111.0) AppleWebKit/536.11 "
    "(KHTML, like Gecko) Chrome/20.0.1132.57 Safari/536.11",
    "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/536.6 "
    "(KHTML, like Gecko) Chrome/20.0.1092.0 Safari/536.6",
    "Mozilla/5.0 (Windows NT 6.2) AppleWebKit/536.6 "
    "(KHTML, like Gecko) Chrome/20.0.1090.0 Safari/536.6",
    "Mozilla/5.0 (Windows NT 6.2; WOW64) AppleWebKit/537.1 "
    "(KHTML, like Gecko) Chrome/19.77.34.5 Safari/537.1",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/536.5 "
    "(KHTML, like Gecko) Chrome/19.0.1084.9 Safari/536.5",
    "Mozilla/5.0 (Windows NT 6.0) AppleWebKit/536.5 "
    "(KHTML, like Gecko) Chrome/19.0.1084.36 Safari/536.5",
    "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/536.3 "
    "(KHTML, like Gecko) Chrome/19.0.1063.0 Safari/536.3",
    "Mozilla/5.0 (Windows NT 5.1) AppleWebKit/536.3 "
    "(KHTML, like Gecko) Chrome/19.0.1063.0 Safari/536.3",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_8_0) AppleWebKit/536.3 "
    "(KHTML, like Gecko) Chrome/19.0.1063.0 Safari/536.3",
    "Mozilla/5.0 (Windows NT 6.2) AppleWebKit/536.3 "
    "(KHTML, like Gecko) Chrome/19.0.1062.0 Safari/536.3",
    "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/536.3 "
    "(KHTML, like Gecko) Chrome/19.0.1062.0 Safari/536.3",
    "Mozilla/5.0 (Windows NT 6.2) AppleWebKit/536.3 "
    "(KHTML, like Gecko) Chrome/19.0.1061.1 Safari/536.3",
    "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/536.3 "
    "(KHTML, like Gecko) Chrome/19.0.1061.1 Safari/536.3",
    "Mozilla/5.0 (Windows NT 6.1) AppleWebKit/536.3 "
    "(KHTML, like Gecko) Chrome/19.0.1061.1 Safari/536.3",
    "Mozilla/5.0 (Windows NT 6.2) AppleWebKit/536.3 "
    "(KHTML, like Gecko) Chrome/19.0.1061.0 Safari/536.3",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/535.24 "
    "(KHTML, like Gecko) Chrome/19.0.1055.1 Safari/535.24",
    "Mozilla/5.0 (Windows NT 6.2; WOW64) AppleWebKit/535.24 "
    "(KHTML, like Gecko) Chrome/19.0.1055.1 Safari/535.24"
]


class UserAgent(UserAgentMiddleware):

    def process_request(self, request, spider):
        request.headers.setdefault('User-Agent', random.choice(user_agent_list))


class IPAgent:
    _ips_list = list()
    _ips_path = 'paper:'

    @staticmethod
    def get_ip_from_ip_proxy_pool():
        res = requests.get('http://134.175.16.232:5010/get').json()
        while len(res) != 8:
            time.sleep(3)
            logging.info('\t有效IP为空，等待新ip加入\t')
            res = requests.get('http://134.175.16.232:5010/get').json()
            logging.info('\t等待3s结束\t')
        logging.info('\t{} 代理启用\t'.format(res['proxy']))
        return res['proxy']

    def process_request(self, request, spider):
        request.meta['proxy'] = self.get_ip_from_ip_proxy_pool()


class TaiYangIpAgent:

    def __init__(self):
        pass


# class Reset:
#
#     def process_request(self, request, spider):
#         if re.search(r'wulingb', request.url):
#             if not Spider.CONN.llen(Spider.redis_key):
#                 logging.info('{} 没有重定向站点，可以请求'.format(request.url))
#                 Spider.CONN.rpush(Spider.redis_key, request.url)
#             else:
#                 logging.info('{} 有重定向站点，无法请求'.format(request.url))
#                 return TextResponse(url=request.url, request=request)


class Catch302:

    _catch_code = (302, )

    def process_response(self, request, response, spider):
        logging.info('\t发生302重定向')
        if response.status in self._catch_code:
            location = safe_url_string(response.headers['location'])
            redirected_url = urljoin(request.url, location)
            logging.info('\t{}-->{}'.format(response.url, redirected_url))
            # with self_redis.get_redis_conn() as conn:
            #     conn.rpush(redis_key, )
            print(response.url, request.url, redirected_url)

