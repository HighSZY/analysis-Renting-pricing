# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import re
import scrapy
from scrapy.loader.processors import *


def get_id(x):
    return re.search(r'\d+', x).group(0)


def get_space_area(x):
    data = re.search(r'\w+', x)
    if data is None:
        return ''
    else:
        return data.group(0) if data.group(0) != '小区' else ''


def get_space_split_middle_line_address(x):
    data_list = re.findall(r'\w+', x)
    data = '-'.join(data_list[1:])
    return data


def get_space_split_middle_line_area(x):
    data_list = re.findall(r'\w+', x)
    data = '-'.join(data_list[0:1])
    return data


def get_space_rule(x):
    return x.replace('-', '')


def get_space_high(x):
    try:
        return re.search(r'(\w+)\(', x).group(1)
    except:
        return '低层'


class LunwenBaseItem(scrapy.Item):
    id = scrapy.Field(
        input_processor=Compose(TakeFirst(), get_id),
        output_processor=TakeFirst()
    )
    name = scrapy.Field(
        input_processor=Join(''),
        output_processor=TakeFirst()
    )
    space_area = scrapy.Field(
        input_processor=MapCompose(get_space_area),
        output_processor=Compose(Join('-'), get_space_split_middle_line_area)
    )
    space_rule = scrapy.Field(
        input_processor=Join('-'),
        output_processor=Compose(TakeFirst(), get_space_rule)
    )
    space_size = scrapy.Field(
        output_processor=TakeFirst(),
    )
    address = scrapy.Field(
        input_processor=MapCompose(get_space_area),
        output_processor=Compose(Join('-'), get_space_split_middle_line_address)
    )
    upload_time = scrapy.Field(
        output_processor=TakeFirst(),
    )
    pricing = scrapy.Field(
        output_processor=TakeFirst(),
    )
    space_high = scrapy.Field(
        output_processor=Compose(TakeFirst(), get_space_high),
    )
    rent_type = scrapy.Field(
        output_processor=TakeFirst(),
    )
