# -*- coding: utf-8 -*-
import codecs
import re

def load_filter_list():
    with codecs.open('config/filter_title', 'r', encoding='utf-8') as f:
        filter_list = f.readlines()
    return filter_list

def filter_title(title, title_filter_list):
    if len(title.strip()) == 0:
        return False
    for item in title_filter_list:
        if item.strip() in title:
            return False
    if len(re.findall("([0-9]*)月([0-9]*)日", title)) > 0:
        return False
    if '同比' in title and '净利' in title:
        return False
    if '同比' in title and '利润' in title:
        return False
    if '同比' in title and '产量' in title:
        return False
    if '同比' in title and '增长' in title:
        return False
    if '营收' in title and '净利' in title:
        return False
    if '快讯' in title and '报于' in title:
        return False
    if '目标价' in title and '评级' in title:
        return False
    if '买入' in title and '评级' in title:
        return False
    if '增持' in title and '评级' in title:
        return False
    if '维持' in title and '评级' in title:
        return False
    if '质押' in title and '万股票' in title:
        return False
    if '本周国内' in title and '价格' in title:
        return False
    if '利润' in title or '净利' in title and '降' in title or '减' in title or '增' in title or '涨' in title:
        print(1)
        return False
    if '营收' in title and '净赚' in title:
        return False
    if '质押' in title and '股' in title:
        return False
    return True


title = '国家统计局：2018年经济总量突破90万亿GDP增速6.6%'
title_filter_list = load_filter_list()
x = filter_title(title, title_filter_list)
print(x)







