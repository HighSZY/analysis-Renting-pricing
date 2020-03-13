# -*- coding: utf-8 -*-
import logging
import re


# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html
import pymysql as pq
from .database import self_mysql


class LunwenPipeline:

    @staticmethod
    def decorate_upload_time(time):
        time_list = re.findall(r'\d+', time)
        year = 2020 if len(time_list) < 1 else time_list[0]
        month = 3 if len(time_list) < 2 else time_list[1]
        day = 1 if len(time_list) < 3 else time_list[2]
        return '{}-{}-{}'.format(
            year, month, day
        )

    @staticmethod
    def decorate_space_size(space_size):
        return re.search(r'\d+(\.\d+)?', space_size).group(0)

    def process_item(self, item, spider):
        sql = """
                insert into roomInfo
                    (id, name , pricing, upload_time, address, space_area, space_size, space_rule, space_high, rent_type, url)
                    values ('%s', '%s', '%d', date_format('%s 0:0:0', '%%Y-%%m-%%d %%H:%%i:%%s'), '%s', '%s', '%f', '%s', '%s', '%s', '%s');
              """
        self_mysql.exec(sql % (
                        item['id'], item['name'], int(item['pricing']),
                        self.decorate_upload_time(item['upload_time']),
                        item['address'],
                        item['space_area'],
                        float(self.decorate_space_size(item['space_size'])),
                        item['space_rule'],
                        item['space_high'],
                        item['rent_type'],
                        item['url']
                    ))

    def close_spider(self, spider):
        self_mysql.conn.close()


if __name__ == '__main__':
    test = LunwenPipeline()
    test.process_item('', '')
