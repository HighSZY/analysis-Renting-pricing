import base64
import logging
import os
import re

import redis
import requests
from fontTools.ttLib import TTFont
from lxml import etree
from scrapy.linkextractors.lxmlhtml import LxmlLinkExtractor
from scrapy.loader import ItemLoader
from scrapy.selector import Selector
from scrapy_redis.spiders import RedisSpider

from ..items import LunwenBaseItem


class Spider(RedisSpider):
    name = "paper"
    redis_key = 'paper:start_urls'
    _link_extractor = LxmlLinkExtractor(
        allow=['isauction'], allow_domains='chd.zu.anjuke.com',
        restrict_xpaths=['//div[@class="maincontent"]'], unique=True
    )
    _base_path = os.getcwd()
    REDIS_POOL = redis.ConnectionPool(host='134.175.16.232', port=6379, password='2168', db=0)
    CONN = redis.Redis(connection_pool=REDIS_POOL)

    def _font_secret_parse(self, response):
        def remove_fail_ip(request):
            logging.info('\t失效移除，准备移除\t')
            res = None
            try:
                res = requests.get('http://134.175.16.232:5010/delete?proxy={}'.format(request.meta['proxy'][2:]))
            except Exception as e:
                logging.info('\t移除失败{}\t'.format(e))
            if res.status_code == 200:
                logging.info('\t移除成功\t')
            else:
                logging.info('\t移除失败{}\t'.format(res.status_code))

        def _get_font():
            try:
                base64_string = response.text.split("base64,")[1].split("'")[0].strip()
            except IndexError:
                logging.info('\t网页识别出爬虫\t')
                remove_fail_ip(response.request)
                request = response.request.copy()
                logging.info('\turl重新返回调度器{}\t'.format(request))
                return [request]
            logging.info('\t解析base64_string {}\t'.format(base64_string))
            # 将 base64 编码的字体字符串解码成二进制编码
            bin_data = base64.decodebytes(base64_string.encode())
            # 保存为字体文件
            with open(self._base_path + '/58font.woff', 'wb') as f:
                f.write(bin_data)
            logging.info('\t字体文件保存成功！\t')
            # 获取字体文件，将其转换为xml文件
            font = TTFont(self._base_path + '/58font.woff')
            font.saveXML(self._base_path + '/58font.xml')
            logging.info('\t已成功将字体文件转换为xml文件！\t')
            return response

        def _find_font():
            glyph_list = {
                'glyph00001': '0',
                'glyph00002': '1',
                'glyph00003': '2',
                'glyph00004': '3',
                'glyph00005': '4',
                'glyph00006': '5',
                'glyph00007': '6',
                'glyph00008': '7',
                'glyph00009': '8',
                'glyph00010': '9'
            }
            # 十个加密字体编码
            unicode_list = ['0x9476', '0x958f', '0x993c', '0x9a4b', '0x9e3a', '0x9ea3', '0x9f64', '0x9f92', '0x9fa4',
                            '0x9fa5']
            num_list = []
            # 利用xpath语法匹配xml文件内容
            font_data = etree.parse(self._base_path + '/58font.xml')
            for unicode in unicode_list:
                # 依次循环查找xml文件里code对应的name
                result = font_data.xpath("//cmap//map[@code='{}']/@name".format(unicode))[0]
                # print(result)
                # 循环字典的key，如果code对应的name与字典的key相同，则得到key对应的value
                for key in glyph_list.keys():
                    if key == result:
                        num_list.append(glyph_list[key])
            logging.info('\t已成功找到编码所对应的数字 {}\t'.format(num_list))
            # print(num_list)
            # 返回value列表
            return num_list

        _get_font()
        num = _find_font()
        logging.info('\t字体替换开始---doing---\t')
        text = response.text.replace('&#x9476;', num[0]). \
            replace('&#x958f;', num[1]).replace('&#x993c;', num[2]). \
            replace('&#x9a4b;', num[3]).replace('&#x9e3a;', num[4]). \
            replace('&#x9ea3;', num[5]).replace('&#x9f64;', num[6]). \
            replace('&#x9f92;', num[7]).replace('&#x9fa4;', num[8]). \
            replace('&#x9fa5;', num[9])
        logging.info('\t字体替换完成---done---\t')
        return text

    def parse(self, response):
        # https://chd.zu.anjuke.com/fangyuan/wulingb/p1
        # https://chd.zu.anjuke.com/fangyuan/1216188580421633?isauction=1&shangquan_id=25877
        url = response.request.url
        url = url[0: -1] if url[-1] == '/' else url
        page_name = os.path.basename(url)
        logging.info('\t分析网页组成 {}\t'.format(url))
        if re.search(r'wulingb', url):
            links = self._link_extractor.extract_links(response)
            logging.info('\tl页面{}，成功获取第二层 {} 页面链接\n\t'.format(page_name, links))
            for link in links:
                self.CONN.rpush(self.redis_key, link.url)
            logging.info('\t第二层链接装载成功---done---\t')
            next_url = Selector(response=response)
            next_url = next_url.xpath('//i[@class="aDotted"]/following-sibling::a/@href').extract_first()
            if next_url is None:
                if re.search(r'\d+', page_name).group(0) == 10:
                    logging.info('当前页面为{},正常结束'.format(page_name))
                else:
                    logging.info('当前页面为{},非正常结束！！！！！'.format(page_name))
            else:
                self.CONN.rpush(self.redis_key, next_url)
                logging.info('\t{}写入->Redis'.format(next_url))
        else:
            return self.parse_main_page(response)

    def parse_main_page(self, response):
        self.record_request_info(response)
        logging.info('\t分析详细数据ing---{}\t'.format(response.request.url))
        selector = Selector(text=self._font_secret_parse(response))
        item_loader = ItemLoader(item=LunwenBaseItem(), response=response, selector=selector)
        item_loader.add_xpath('id',
                              '//div[@class="right-info"]/span/text()')
        item_loader.add_xpath('name',
                              '//h3[@class="house-title"]/div[@class="strongbox"]/text()')
        item_loader.add_xpath('space_area',
                              '//li[contains(@class, "house-info-item")][7]//text()')
        item_loader.add_xpath('space_rule',
                              '//li[contains(@class, "house-info-item")][1]//span[@class="info"]//text()')
        item_loader.add_xpath('space_size',
                              '//li[contains(@class, "house-info-item")][2]//span[@class="info"]//text()')
        item_loader.add_xpath('address',
                              '//li[contains(@class, "house-info-item")][7]//text()')
        item_loader.add_xpath('upload_time',
                              '//div[@class="right-info"]/b/text()')
        item_loader.add_xpath('pricing',
                              '//span[@class="price"]//b/text()')
        item_loader.add_xpath('rent_type',
                              '//li[@class="title-label-item rent"]/text()')
        item_loader.add_xpath('space_high',
                              '//li[contains(@class, "house-info-item")][4]/span[@class="info"]/text()')
        return item_loader.load_item()
        # print(item_loader.load_item())

    def record_request_info(self, response):
        if response.status == 200:
            with open(self._base_path + '/request_info.txt', mode='a+') as file:
                request = response.request
                request_time = 0
                try:
                    request_time = request.meta['retry_times']
                except Exception as e:
                    logging.info('{}'.format(e))
                line = '\t{}\t\n\t一共请求次数：{}\t\n\t最终请求成功: {}\t'.format(request,
                                                                      request_time,
                                                                      response.status)
                file.writelines(line)
                logging.info('\t本条请求记录在册\t')
