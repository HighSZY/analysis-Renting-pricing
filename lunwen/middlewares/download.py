import redis
import requests
import re
import logging
import time

import random
import logging
import random
import re
import time

import requests
from scrapy.downloadermiddlewares.useragent import UserAgentMiddleware

from ..database import *

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
            time.sleep(100)
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

from scrapy.downloadermiddlewares.redirect import BaseRedirectMiddleware
from six.moves.urllib.parse import urljoin
from w3lib.url import safe_url_string


class Catch302(BaseRedirectMiddleware):
    _catch_code = (302,)

    def process_response(self, request, response, spider):
        if (request.meta.get('dont_redirect', False) or
                response.status in getattr(spider, 'handle_httpstatus_list', []) or
                response.status in request.meta.get('handle_httpstatus_list', []) or
                request.meta.get('handle_httpstatus_all', False)):
            return response

        allowed_status = (301, 302, 303, 307, 308)
        if 'Location' not in response.headers or response.status not in allowed_status:
            return response

        location = safe_url_string(response.headers['location'])

        redirected_url = urljoin(request.url, location)

        if response.status in self._catch_code and re.search(r'namespace=anjuke_zufang_detail_pc', redirected_url):
            logging.info('\t302到防爬站，将地址重新写入redis')
            self_redis.exec_rpush(redis_key, request.url)
            return response

        if response.status in (301, 307, 308) or request.method == 'HEAD':
            redirected = request.replace(url=redirected_url)
            return self._redirect(redirected, request, spider, response.status)

        redirected = self._redirect_request_using_get(request, redirected_url)
        return self._redirect(redirected, request, spider, response.status)


from scrapy.downloadermiddlewares.retry import RetryMiddleware


class RemoveInvalidIp(RetryMiddleware):

    def _retry(self, request, reason, spider):
        remove_fail_ip(request)
        return super()._retry(request, reason, spider)
