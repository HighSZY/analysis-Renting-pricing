import logging
import socket

import requests

from .mysql import SelfMysql
from .redis import SelfRedis

redis_key = 'paper:start_urls'

self_redis = SelfRedis(host='134.175.16.232',
                       port=6379,
                       password='2168',
                       db=0,
                       socket_connect_timeout=9999,
                       socket_keepalive=True,
                       socket_keepalive_options={
                           socket.SO_KEEPALIVE: 60,
                           socket.TCP_KEEPCNT: 9
})

self_mysql = SelfMysql(host='134.175.16.232',
                       user='sunzeyu',
                       password='2168',
                       database='lunwen'
)


def remove_fail_ip(request):
    logging.info('\t失效移除，准备移除\t')
    res = None
    try:
        res = requests.get('http://134.175.16.232:5010/delete?proxy={}'.format(request.meta['proxy'][2:]))
    except Exception as e:
        logging.info('\t移除失败{}\t'.format(e))
    if res.status_code == 200:
        logging.info('\t{} 移除成功\t'.format(request.meta['proxy'][2:]))
    else:
        logging.info('\t移除失败{}\t'.format(res.status_code))


def redirect_302(response, request, redirected_url):
    if response.status == 302:
        logging.info('\t出现重定向现象\t')
        logging.info('\t{}---->{}t'.format(request.url, redirected_url))
        logging.info('\t重新写入\t')
        with self_redis.get_redis_conn() as cursor:
            cursor.rpush('paper:start_urls', request.url)
        logging.info('\t数据被重新写入Redis\t')