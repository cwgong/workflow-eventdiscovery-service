# -*- coding: utf-8 -*-

import json
import re
import time
import io
import requests
import datetime

class Date_chunk_handle:

    def __init__(self):
        self.orderby_rgx = None
        self.key_words_time = ['上午','中午','晚上','下午','晨','晚','全天']
        self.key_words_type = ['报道','消息','讯','获悉','公布']
        self.time_trigger_words = ['日','日电','日和']
        self.seg_trigger_words = ['-','到','至','和','—','－']
        self.Chinese_num = ['一', '二', '三', '四', '五', '六', '七', '八', '九', '十', '十一', '十二', '十三', '十四', '十五', '十六', '十七', '十八',
                       '十九', '二十', '二十一', '二十二', '二十三', '二十四', '二十五', '二十六', '二十七', '二十八', '二十九', '三十', '三十一']
        self.rule = ["([0-9零一二两三四五六七八九十]+年)", "([0-9一二两三四五六七八九十]+月)", "([0-9一二两三四五六七八九十]+[号日])"]


        week_time_rgx = '星期|周'
        hour_time_rgx = '时|点'
        period_time_rgx = '上午|中午|晚上|下午|晨|晚|全天'
        time_type_rgx = '报道|消息|讯|获悉|公布|电|号'
        chinese_num_rgx = '零一二两三四五六七八九十'
        year_chinese_num_rgx = '[零一二两三四五六七八九十]{1,4}'
        month_chinese_num_rgx = '[零一二两三四五六七八九十]{1,2}'
        seg_trigger_rgx = '-|到|至|—|和|－'
        year_arab_num_rgx = '\d{1,4}'
        month_arab_num_rgx = '\d{1,2}'
        anyway_rgx_year = '.{,7}'
        anyway_rgx_month = '.{,2}'
        anyway_rgx_seg = '.{,9}'
        anyway_rgx_day1 = '.{,11}'
        anyway_rgx_day2 = '.{,5}'


        self.normalize_chunk = re.compile(r'(.*)({0})(.*)'.format(seg_trigger_rgx))

        integrity_1_0 = re.compile(r'({0}年|{2}年)({3}?)(日)({1})'.format(year_chinese_num_rgx,time_type_rgx,year_arab_num_rgx,anyway_rgx_year))

        integrity_1_1 = re.compile(
            r'({0}月|{2}月)({3})(日)({1})'.format(month_chinese_num_rgx, time_type_rgx, month_arab_num_rgx,anyway_rgx_month))

        integrity_1_2 = re.compile(
            r'({0}日|{2}日)({1})'.format(month_chinese_num_rgx, time_type_rgx, month_arab_num_rgx))

        integrity_2 = re.compile(                                                                                       #s = '去年是2019年5月21日（星期五）下午8点到2019年5月22日（星期六）上午9时一起去吃饭'
            r'({0}年|{5}年)({7})(日)(?!{6})({8})({1})({9})(日)(?!{6})[(|（](.*?)[)|）]({2})({3}{4}|{10}{4})'.format(year_chinese_num_rgx,          #s = '去年是二零一九年5月21日（星期五）下午8点到2019年5月22日（星期六）上午9时一起去吃饭'
                                                                                               seg_trigger_rgx,
                                                                                               period_time_rgx,
                                                                                         month_chinese_num_rgx,
                                                                                               hour_time_rgx,
                                                                                          year_arab_num_rgx,
                                                                                            time_type_rgx,
                                                                                            anyway_rgx_year,
                                                                                           anyway_rgx_seg,
                                                                                           anyway_rgx_day1,
                                                                                            month_arab_num_rgx))

        integrity_3 = re.compile(
            r'({0}月|{4}月)({6})(日)(?!{5})({7})({1})({8})(日)(?!{5})[(|（](.*?)[)|）]({2})({0}{3}|{4}{3})'.format(month_chinese_num_rgx,           #s = '去年是5月21日（星期五）下午8点到2019年5月22日（星期六）上午9时一起去吃饭'
                                                                                    seg_trigger_rgx,                     #s = '去年是五月21日（星期五）下午8点到2019年5月22日（星期六）上午9时一起去吃饭'
                                                                                    period_time_rgx
                                                                                    ,hour_time_rgx,
                                                                                    month_arab_num_rgx,
                                                                                    time_type_rgx,
                                                                                     anyway_rgx_day2,
                                                                                     anyway_rgx_seg,
                                                                                     anyway_rgx_day1))

        integrity_4 = re.compile(
            r'({0}日|{4}日)(?!{5})({6})({1})({7})(日)(?!{5})[(|（](.*?)[)|）]({2})({0}{3}|{4}{3})'.format(month_chinese_num_rgx,              #s = '去年是21日（星期五）下午8点到2019年5月22日（星期六）上午9时一起去吃饭
                                                                                    seg_trigger_rgx,                    #s = '去年是二十一日（星期五）下午8点到2019年5月22日（星期六）上午9时一起去吃饭
                                                                                    period_time_rgx
                                                                                    , hour_time_rgx,
                                                                                month_arab_num_rgx,
                                                                                  time_type_rgx,
                                                                                  anyway_rgx_seg,
                                                                                  anyway_rgx_day1))

        integrity_5 = re.compile(
            r'({0}年|{3}年)({7})(日)(?!{4})({5})({1})({6})(日)(?!{4})[(|（](.*?)[)|）]({2})'.format(year_chinese_num_rgx,                 #s = '去年是2019年21日（星期五）下午8点到2019年5月22日（星期六）上午一起去吃饭
                                                                              seg_trigger_rgx,                          #s = '去年是二零一九年21日（星期五）下午8点到2019年5月22日（星期六）上午一起去吃饭
                                                                              period_time_rgx,
                                                                              year_arab_num_rgx,
                                                                              time_type_rgx,
                                                                              anyway_rgx_seg,
                                                                              anyway_rgx_day1,
                                                                              anyway_rgx_year))

        integrity_6 = re.compile(
            r'({0}年|{5}年)({8})(日)(?!{7})({9})({1})({10})(日)(?!{7})[(|（](.*?)[)|）]({3}{4}|{6}{4})'.format(year_chinese_num_rgx,           #s = '去年是2019年21日（星期五）下午8点到2019年5月22日（星期六）8点一起去吃饭
                                                                                    seg_trigger_rgx,                    #s = '去年是二零一九年21日（星期五）下午8点到2019年5月22日（星期六）八点一起去吃饭
                                                                                    period_time_rgx,
                                                                                    month_chinese_num_rgx,
                                                                                    hour_time_rgx,
                                                                                    year_arab_num_rgx,
                                                                                    month_arab_num_rgx,
                                                                                    time_type_rgx,
                                                                                    anyway_rgx_year,
                                                                                    anyway_rgx_seg,
                                                                                    anyway_rgx_day1))

        integrity_7 = re.compile(
            r'({0}年|{5}年)({8})(日)(?!{7})({9})({1})({10})(日)(?!{7})[(|（](.*?)[)|）]'.format(year_chinese_num_rgx,           #s = '去年是2019年21日（星期五）下午8点到2019年5月22日（星期六）一起去吃饭
                                                                                    seg_trigger_rgx,                    #s = '去年是二零一九年21日（星期五）下午8点到2019年5月22日（星期六）一起去吃饭
                                                                                    period_time_rgx,
                                                                                    month_chinese_num_rgx,
                                                                                    hour_time_rgx,
                                                                                    year_arab_num_rgx,
                                                                                    month_arab_num_rgx,
                                                                                    time_type_rgx,anyway_rgx_year,
                                                                                    anyway_rgx_seg,
                                                                                    anyway_rgx_day1))

        integrity_8 = re.compile(
            r'({0}年|{5}年)({8})(日)(?!{7})({9})({1})({10})(日)(?!{7})({3}{4}|{6}{4})'.format(year_chinese_num_rgx,
                                                                         # s = '去年是2019年21日（星期五）下午8点到2019年5月22日8点一起去吃饭
                                                                         seg_trigger_rgx,
                                                                         # s = '去年是二零一九年21日（星期五）下午8点到2019年5月22日八点一起去吃饭
                                                                         period_time_rgx,
                                                                         month_chinese_num_rgx,
                                                                         hour_time_rgx,
                                                                         year_arab_num_rgx,
                                                                         month_arab_num_rgx,
                                                                         time_type_rgx,anyway_rgx_year,
                                                                         anyway_rgx_seg,
                                                                         anyway_rgx_day1))

        integrity_9 = re.compile(
            r'({0}年|{5}年)({8})(日)(?!{7})({9})({1})({10})(日)(?!{7})({2})'.format(year_chinese_num_rgx,
                                                                     # s = '去年是2019年21日（星期五）下午8点到2019年5月22日上午一起去吃饭
                                                                     seg_trigger_rgx,
                                                                     # s = '去年是二零一九年21日（星期五）下午8点到2019年5月22日上午一起去吃饭
                                                                     period_time_rgx,
                                                                     month_chinese_num_rgx,
                                                                     hour_time_rgx,
                                                                     year_arab_num_rgx,
                                                                     month_arab_num_rgx,
                                                                     time_type_rgx,anyway_rgx_year,
                                                                     anyway_rgx_seg,
                                                                     anyway_rgx_day1))

        integrity_23 = re.compile(
            r'({0}年|{5}年)({8})(日)(?!{7})({9})({1})({10})(日)(?!{7})'.format(year_chinese_num_rgx,
                                                               # s = '去年是2019年21日（星期五）下午8点到2019年5月22日一起去吃饭
                                                               seg_trigger_rgx,
                                                               # s = '去年是二零一九年21日（星期五）下午8点到2019年5月22日一起去吃饭
                                                               period_time_rgx,
                                                               month_chinese_num_rgx,
                                                               hour_time_rgx,
                                                               year_arab_num_rgx,
                                                               month_arab_num_rgx,
                                                               time_type_rgx,anyway_rgx_year,
                                                                anyway_rgx_seg,
                                                                anyway_rgx_day1))

        integrity_10 = re.compile(
            r'({0}年|{5}年)({8})(日)(?!{7})({9})({1})({10})(日)(?!{7})({2})({3}{4}|{6}{4})'.format(year_chinese_num_rgx,
                                                               # s = '去年是2019年21日（星期五）下午8点到2019年5月22日上午八点一起去吃饭
                                                               seg_trigger_rgx,
                                                               # s = '去年是二零一九年21日（星期五）下午8点到2019年5月22日上午8点一起去吃饭
                                                               period_time_rgx,
                                                               month_chinese_num_rgx,
                                                               hour_time_rgx,
                                                               year_arab_num_rgx,
                                                               month_arab_num_rgx,
                                                               time_type_rgx,anyway_rgx_year,
                                                                anyway_rgx_seg,
                                                                anyway_rgx_day1))

        integrity_11 = re.compile(
            r'({3}月|{6}月)({8})(日?!{7})(?!{7})({9})({1})({10})(日)(?!{7})[(|（](.*?)[)|）]({2})'.format(year_chinese_num_rgx,
                                                                          # s = '去年是5月21日（星期五）下午8点到2019年5月22日（星期六）上午一起去吃饭
                                                                          seg_trigger_rgx,
                                                                          # s = '去年是五月21日（星期五）下午8点到2019年5月22日（星期六）上午一起去吃饭
                                                                          period_time_rgx,
                                                                          month_chinese_num_rgx,
                                                                          hour_time_rgx,
                                                                          year_arab_num_rgx,
                                                                          month_arab_num_rgx,
                                                                          time_type_rgx,
                                                                          anyway_rgx_day2,anyway_rgx_seg,
                                                                          anyway_rgx_day1))

        integrity_12 = re.compile(
            r'({3}月|{6}月)({8})(日)(?!{7})({9})({1})({10})(日)(?!{7})[(|（](.*?)[)|）]({3}{4}|{6}{4})'.format(year_chinese_num_rgx,
                                                                              # s = '去年是5月21日（星期五）下午8点到2019年5月22日（星期六）8点一起去吃饭
                                                                              seg_trigger_rgx,
                                                                              # s = '去年是五月21日（星期五）下午8点到2019年5月22日（星期六）八点一起去吃饭
                                                                              period_time_rgx,
                                                                              month_chinese_num_rgx,
                                                                              hour_time_rgx,
                                                                              year_arab_num_rgx,
                                                                              month_arab_num_rgx,
                                                                              time_type_rgx,
                                                                          anyway_rgx_day2,anyway_rgx_seg,
                                                                          anyway_rgx_day1))

        integrity_13 = re.compile(
            r'({3}月|{6}月)({8})(日)(?!{7})({9})({1})({10})(日)(?!{7})[(|（](.*?)[)|）]'.format(year_chinese_num_rgx,
                                                                                    # s = '去年是5月21日（星期五）下午8点到2019年5月22日（星期六）一起去吃饭
                                                                                    seg_trigger_rgx,
                                                                                    # s = '去年是五月21日（星期五）下午8点到2019年5月22日（星期六）一起去吃饭
                                                                                    period_time_rgx,
                                                                                    month_chinese_num_rgx,
                                                                                    hour_time_rgx,
                                                                                    year_arab_num_rgx,
                                                                                    month_arab_num_rgx,
                                                                                    time_type_rgx,
                                                                          anyway_rgx_day2,anyway_rgx_seg,
                                                                          anyway_rgx_day1))

        integrity_14 = re.compile(
            r'({3}月|{6}月)({8})(日)(?!{7})({9})({1})({10})(日)(?!{7})({3}{4}|{6}{4})'.format(year_chinese_num_rgx,
                                                                         # s = '去年是5月21日（星期五）下午8点到2019年5月22日8点一起去吃饭
                                                                         seg_trigger_rgx,
                                                                         # s = '去年是五月21日（星期五）下午8点到2019年5月22日八点一起去吃饭
                                                                         period_time_rgx,
                                                                         month_chinese_num_rgx,
                                                                         hour_time_rgx,
                                                                         year_arab_num_rgx,
                                                                         month_arab_num_rgx,
                                                                         time_type_rgx,
                                                                          anyway_rgx_day2,anyway_rgx_seg,
                                                                          anyway_rgx_day1))

        integrity_15 = re.compile(
            r'({3}月|{6}月)({8})(日)(?!{7})({9})({1})({10})(日)(?!{7})({2})'.format(year_chinese_num_rgx,
                                                                     # s = '去年是5月21日（星期五）下午8点到2019年5月22日上午一起去吃饭
                                                                     seg_trigger_rgx,
                                                                     # s = '去年是五月21日（星期五）下午8点到2019年5月22日上午一起去吃饭
                                                                     period_time_rgx,
                                                                     month_chinese_num_rgx,
                                                                     hour_time_rgx,
                                                                     year_arab_num_rgx,
                                                                     month_arab_num_rgx,
                                                                     time_type_rgx,
                                                                     anyway_rgx_day2,anyway_rgx_seg,
                                                                     anyway_rgx_day1))

        integrity_24 = re.compile(
            r'({3}月|{6}月)({8})(日)(?!{7})({9})({1})({10})(日)(?!{7})'.format(year_chinese_num_rgx,
                                                               # s = '去年是5月21日（星期五）下午8点到2019年5月22日一起去吃饭
                                                               seg_trigger_rgx,
                                                               # s = '去年是五月21日（星期五）下午8点到2019年5月22日一起去吃饭
                                                               period_time_rgx,
                                                               month_chinese_num_rgx,
                                                               hour_time_rgx,
                                                               year_arab_num_rgx,
                                                               month_arab_num_rgx,
                                                               time_type_rgx,
                                                               anyway_rgx_day2,anyway_rgx_seg,
                                                               anyway_rgx_day1))

        integrity_16 = re.compile(
            r'({3}月|{6}月)({8})(日)(?!{7})({9})({1})({10})(日)(?!{7})({2})({3}{4}|{6}{4})'.format(year_chinese_num_rgx,
                                                               # s = '去年是5月21日（星期五）下午8点到2019年5月22日上午8点一起去吃饭
                                                               seg_trigger_rgx,
                                                               # s = '去年是五月21日（星期五）下午8点到2019年5月22日上午8点一起去吃饭
                                                               period_time_rgx,
                                                               month_chinese_num_rgx,
                                                               hour_time_rgx,
                                                               year_arab_num_rgx,
                                                               month_arab_num_rgx,
                                                               time_type_rgx,
                                                               anyway_rgx_day2,anyway_rgx_seg,
                                                               anyway_rgx_day1))

        integrity_17 = re.compile(
            r'({0}日|{6}日)(?!{7})({8})({1})({9})(日)(?!{7})[(|（](.*?)[)|）]({2})'.format(year_chinese_num_rgx,
                                                                          # s = '去年是21日（星期五）下午8点到2019年5月22日（星期六）上午一起去吃饭
                                                                          seg_trigger_rgx,
                                                                          # s = '去年是二十一日（星期五）下午8点到2019年5月22日（星期六）上午一起去吃饭
                                                                          period_time_rgx,
                                                                          month_chinese_num_rgx,
                                                                          hour_time_rgx,
                                                                          year_arab_num_rgx,
                                                                          month_arab_num_rgx,
                                                                          time_type_rgx,anyway_rgx_seg,
                                                                          anyway_rgx_day1))

        integrity_18 = re.compile(
            r'({0}日|{6}日)(?!{7})({8})({1})({9})(日)(?!{7})[(|（](.*?)[)|）]({3}{4}|{6}{4})'.format(year_chinese_num_rgx,
                                                                       # s = '去年是21日（星期五）下午8点到2019年5月22日（星期六）8点一起去吃饭
                                                                       seg_trigger_rgx,
                                                                       # s = '去年是二十一日（星期五）下午8点到2019年5月22日（星期六）八点一起去吃饭
                                                                       period_time_rgx,
                                                                       month_chinese_num_rgx,
                                                                       hour_time_rgx,
                                                                       year_arab_num_rgx,
                                                                       month_arab_num_rgx,
                                                                       time_type_rgx,anyway_rgx_seg,
                                                                        anyway_rgx_day1))

        integrity_19 = re.compile(
            r'({0}日|{6}日)(?!{7})({8})({1})({9})(日)(?!{7})[(|（](.*?)[)|）]'.format(year_chinese_num_rgx,
                                                                             # s = '去年是21日（星期五）下午8点到2019年5月22日（星期六）一起去吃饭
                                                                             seg_trigger_rgx,
                                                                             # s = '去年是二十一日（星期五）下午8点到2019年5月22日（星期六）一起去吃饭
                                                                             period_time_rgx,
                                                                             month_chinese_num_rgx,
                                                                             hour_time_rgx,
                                                                             year_arab_num_rgx,
                                                                             month_arab_num_rgx,
                                                                             time_type_rgx,anyway_rgx_seg,
                                                                             anyway_rgx_day1))

        integrity_20 = re.compile(
            r'({0}日|{6}日)(?!{7})({8})({1})({9})(日)(?!{7})({3}{4}|{6}{4})'.format(year_chinese_num_rgx,
                                                                 # s = '去年是21日（星期五）下午8点到2019年5月22日8点一起去吃饭
                                                                 seg_trigger_rgx,
                                                                 # s = '去年是二十一日（星期五）下午8点到2019年5月22日八点一起去吃饭
                                                                 period_time_rgx,
                                                                 month_chinese_num_rgx,
                                                                 hour_time_rgx,
                                                                 year_arab_num_rgx,
                                                                 month_arab_num_rgx,
                                                                 time_type_rgx,anyway_rgx_seg,
                                                                  anyway_rgx_day1))

        integrity_21 = re.compile(
            r'({0}日|{6}日)(?!{7})({8})({1})({9})(日)(?!{7})({2})'.format(year_chinese_num_rgx,
                                                              # s = '去年是21日（星期五）下午8点到2019年5月22日上午一起去吃饭
                                                              seg_trigger_rgx,
                                                              # s = '去年是二十一日（星期五）下午8点到2019年5月22日上午一起去吃饭
                                                              period_time_rgx,
                                                              month_chinese_num_rgx,
                                                              hour_time_rgx,
                                                              year_arab_num_rgx,
                                                              month_arab_num_rgx,
                                                              time_type_rgx,anyway_rgx_seg,
                                                              anyway_rgx_day1))

        integrity_22 = re.compile(
            r'({0}日|{6}日)(?!{7})({8})({1})({9})(日)(?!{7})({2})({3}{4}|{6}{4})'.format(year_chinese_num_rgx,
                                                        # s = '去年是21日（星期五）下午8点到2019年5月22日上午8点一起去吃饭
                                                        seg_trigger_rgx,
                                                        # s = '去年是二十一日（星期五）下午8点到2019年5月22日上午八点一起去吃饭
                                                        period_time_rgx,
                                                        month_chinese_num_rgx,
                                                        hour_time_rgx,
                                                        year_arab_num_rgx,
                                                        month_arab_num_rgx,
                                                        time_type_rgx,anyway_rgx_seg,
                                                        anyway_rgx_day1))

        integrity_25 = re.compile(
            r'({0}日|{6}日)(?!{7})({8})({1})({9})(日)(?!{7})'.format(year_chinese_num_rgx,
                                                                   # s = '去年是21日（星期五）下午8点到2019年5月22日一起去吃饭
                                                                   seg_trigger_rgx,
                                                                   # s = '去年是二十一日（星期五）下午8点到2019年5月22日一起去吃饭
                                                                   period_time_rgx,
                                                                   month_chinese_num_rgx,
                                                                   hour_time_rgx,
                                                                   year_arab_num_rgx,
                                                                   month_arab_num_rgx,
                                                                   time_type_rgx,anyway_rgx_seg,
                                                                   anyway_rgx_day1))

        integrity_50 = re.compile(
            r'({0}|{6})(?!{7})({8})({1})({9})(日)(?!{7})[(|（](.*?)[)|）]({2})'.format(year_chinese_num_rgx,
                                                                                      # s = '去年是21日（星期五）下午8点到2019年5月22日（星期六）上午一起去吃饭
                                                                                      seg_trigger_rgx,
                                                                                      # s = '去年是二十一日（星期五）下午8点到2019年5月22日（星期六）上午一起去吃饭
                                                                                      period_time_rgx,
                                                                                      month_chinese_num_rgx,
                                                                                      hour_time_rgx,
                                                                                      year_arab_num_rgx,
                                                                                      month_arab_num_rgx,
                                                                                      time_type_rgx, anyway_rgx_seg,
                                                                                      anyway_rgx_day1))

        integrity_51 = re.compile(
            r'({0}|{6})(?!{7})({8})({1})({9})(日)(?!{7})[(|（](.*?)[)|）]({3}{4}|{6}{4})'.format(year_chinese_num_rgx,
                                                                                                # s = '去年是21日（星期五）下午8点到2019年5月22日（星期六）8点一起去吃饭
                                                                                                seg_trigger_rgx,
                                                                                                # s = '去年是二十一日（星期五）下午8点到2019年5月22日（星期六）八点一起去吃饭
                                                                                                period_time_rgx,
                                                                                                month_chinese_num_rgx,
                                                                                                hour_time_rgx,
                                                                                                year_arab_num_rgx,
                                                                                                month_arab_num_rgx,
                                                                                                time_type_rgx,
                                                                                                anyway_rgx_seg,
                                                                                                anyway_rgx_day1))

        integrity_52 = re.compile(
            r'({0}|{6})(?!{7})({8})({1})({9})(日)(?!{7})[(|（](.*?)[)|）]'.format(year_chinese_num_rgx,
                                                                                 # s = '去年是21日（星期五）下午8点到2019年5月22日（星期六）一起去吃饭
                                                                                 seg_trigger_rgx,
                                                                                 # s = '去年是二十一日（星期五）下午8点到2019年5月22日（星期六）一起去吃饭
                                                                                 period_time_rgx,
                                                                                 month_chinese_num_rgx,
                                                                                 hour_time_rgx,
                                                                                 year_arab_num_rgx,
                                                                                 month_arab_num_rgx,
                                                                                 time_type_rgx, anyway_rgx_seg,
                                                                                 anyway_rgx_day1))

        integrity_53 = re.compile(
            r'({0}|{6})(?!{7})({8})({1})({9})(日)(?!{7})({3}{4}|{6}{4})'.format(year_chinese_num_rgx,
                                                                                 # s = '去年是21日（星期五）下午8点到2019年5月22日8点一起去吃饭
                                                                                 seg_trigger_rgx,
                                                                                 # s = '去年是二十一日（星期五）下午8点到2019年5月22日八点一起去吃饭
                                                                                 period_time_rgx,
                                                                                 month_chinese_num_rgx,
                                                                                 hour_time_rgx,
                                                                                 year_arab_num_rgx,
                                                                                 month_arab_num_rgx,
                                                                                 time_type_rgx, anyway_rgx_seg,
                                                                                 anyway_rgx_day1))

        integrity_54 = re.compile(
            r'({0}|{6})(?!{7})({8})({1})({9})(日)(?!{7})({2})'.format(year_chinese_num_rgx,
                                                                       # s = '去年是21日（星期五）下午8点到2019年5月22日上午一起去吃饭
                                                                       seg_trigger_rgx,
                                                                       # s = '去年是二十一日（星期五）下午8点到2019年5月22日上午一起去吃饭
                                                                       period_time_rgx,
                                                                       month_chinese_num_rgx,
                                                                       hour_time_rgx,
                                                                       year_arab_num_rgx,
                                                                       month_arab_num_rgx,
                                                                       time_type_rgx, anyway_rgx_seg,
                                                                       anyway_rgx_day1))

        integrity_55 = re.compile(
            r'({0}|{6})(?!{7})({8})({1})({9})(日)(?!{7})({2})({3}{4}|{6}{4})'.format(year_chinese_num_rgx,
                                                                                      # s = '去年是21日（星期五）下午8点到2019年5月22日上午8点一起去吃饭
                                                                                      seg_trigger_rgx,
                                                                                      # s = '去年是二十一日（星期五）下午8点到2019年5月22日上午八点一起去吃饭
                                                                                      period_time_rgx,
                                                                                      month_chinese_num_rgx,
                                                                                      hour_time_rgx,
                                                                                      year_arab_num_rgx,
                                                                                      month_arab_num_rgx,
                                                                                      time_type_rgx, anyway_rgx_seg,
                                                                                      anyway_rgx_day1))

        integrity_56 = re.compile(
            r'({0}|{6})(?!{7})({8})({1})({9})(日)(?!{7})'.format(year_chinese_num_rgx,
                                                                  # s = '去年是21日（星期五）下午8点到2019年5月22日一起去吃饭
                                                                  seg_trigger_rgx,
                                                                  # s = '去年是二十一日（星期五）下午8点到2019年5月22日一起去吃饭
                                                                  period_time_rgx,
                                                                  month_chinese_num_rgx,
                                                                  hour_time_rgx,
                                                                  year_arab_num_rgx,
                                                                  month_arab_num_rgx,
                                                                  time_type_rgx, anyway_rgx_seg,
                                                                  anyway_rgx_day1))

        integrity_26 = re.compile(  # s = '去年是2019年5月21日（星期五）下午8点到2019年5月22日（星期六）上午9时一起去吃饭'
            r'({0}年|{5}年)({7})(日)[(|（](.*?)[)|）]({2})({3}{4}|{8}{4})(?!{6})'.format(year_chinese_num_rgx,
                                                                                         # s = '去年是二零一九年5月21日（星期五）下午8点到2019年5月22日（星期六）上午9时一起去吃饭'
                                                                                         seg_trigger_rgx,
                                                                                         period_time_rgx,
                                                                                         month_chinese_num_rgx,
                                                                                         hour_time_rgx,
                                                                                         year_arab_num_rgx,
                                                                                         time_type_rgx,
                                                                                         anyway_rgx_year,
                                                                                         month_arab_num_rgx))

        integrity_27 = re.compile(
            r'({0}月|{4}月)({6})(日)[(|（](.*?)[)|）]({2})({0}{3}|{4}{3})(?!{5})'.format(month_chinese_num_rgx,
                                                                                         # s = '去年是5月21日（星期五）下午8点到2019年5月22日（星期六）上午9时一起去吃饭'
                                                                                         seg_trigger_rgx,
                                                                                         # s = '去年是五月21日（星期五）下午8点到2019年5月22日（星期六）上午9时一起去吃饭'
                                                                                         period_time_rgx
                                                                                         , hour_time_rgx,
                                                                                         month_arab_num_rgx,
                                                                                         time_type_rgx,
                                                                                         anyway_rgx_day2))

        integrity_28 = re.compile(
            r'({0}日|{4}日)[(|（](.*?)[)|）]({2})({0}{3}|{4}{3})(?!{5})'.format(month_chinese_num_rgx,
                                                                                  # s = '去年是21日（星期五）下午8点到2019年5月22日（星期六）上午9时一起去吃饭
                                                                                  seg_trigger_rgx,
                                                                                  # s = '去年是二十一日（星期五）下午8点到2019年5月22日（星期六）上午9时一起去吃饭
                                                                                  period_time_rgx
                                                                                  , hour_time_rgx,
                                                                                  month_arab_num_rgx,
                                                                                    time_type_rgx))

        integrity_29 = re.compile(
            r'({0}年|{3}年)({5})(日)[(|（](.*?)[)|）]({2})(?!{4})'.format(year_chinese_num_rgx,
                                                                              # s = '去年是2019年21日（星期五）下午8点到2019年5月22日（星期六）上午一起去吃饭
                                                                              seg_trigger_rgx,
                                                                              # s = '去年是二零一九年21日（星期五）下午8点到2019年5月22日（星期六）上午一起去吃饭
                                                                              period_time_rgx,
                                                                              year_arab_num_rgx,
                                                                              time_type_rgx,
                                                                              anyway_rgx_year))

        integrity_30 = re.compile(
            r'({0}年|{5}年)({8})(日)[(|（](.*?)[)|）]({3}{4}|{6}{4})(?!{7})'.format(year_chinese_num_rgx,
                                                                                    # s = '去年是2019年21日（星期五）下午8点到2019年5月22日（星期六）8点一起去吃饭
                                                                                    seg_trigger_rgx,
                                                                                    # s = '去年是二零一九年21日（星期五）下午8点到2019年5月22日（星期六）八点一起去吃饭
                                                                                    period_time_rgx,
                                                                                    month_chinese_num_rgx,
                                                                                    hour_time_rgx,
                                                                                    year_arab_num_rgx,
                                                                                    month_arab_num_rgx,
                                                                                    time_type_rgx,
                                                                                    anyway_rgx_year))

        integrity_31 = re.compile(
            r'({0}年|{5}年)({8})(日)[(|（](.*?)[)|）](?!{7})'.format(year_chinese_num_rgx,
                                                                         # s = '去年是2019年21日（星期五）下午8点到2019年5月22日（星期六）一起去吃饭
                                                                         seg_trigger_rgx,
                                                                         # s = '去年是二零一九年21日（星期五）下午8点到2019年5月22日（星期六）一起去吃饭
                                                                         period_time_rgx,
                                                                         month_chinese_num_rgx,
                                                                         hour_time_rgx,
                                                                         year_arab_num_rgx,
                                                                         month_arab_num_rgx,
                                                                         time_type_rgx,
                                                                         anyway_rgx_year))

        integrity_32 = re.compile(
            r'({0}年|{5}年)({8})(日)({3}{4}|{6}{4})(?!{7})'.format(year_chinese_num_rgx,
                                                                     # s = '去年是2019年21日（星期五）下午8点到2019年5月22日8点一起去吃饭
                                                                     seg_trigger_rgx,
                                                                     # s = '去年是二零一九年21日（星期五）下午8点到2019年5月22日八点一起去吃饭
                                                                     period_time_rgx,
                                                                     month_chinese_num_rgx,
                                                                     hour_time_rgx,
                                                                     year_arab_num_rgx,
                                                                     month_arab_num_rgx,
                                                                     time_type_rgx,
                                                                     anyway_rgx_year))

        integrity_33 = re.compile(
            r'({0}年|{5}年)({8})(日)({2})(?!{7})'.format(year_chinese_num_rgx,
                                                               # s = '去年是2019年21日（星期五）下午8点到2019年5月22日上午一起去吃饭
                                                               seg_trigger_rgx,
                                                               # s = '去年是二零一九年21日（星期五）下午8点到2019年5月22日上午一起去吃饭
                                                               period_time_rgx,
                                                               month_chinese_num_rgx,
                                                               hour_time_rgx,
                                                               year_arab_num_rgx,
                                                               month_arab_num_rgx,
                                                               time_type_rgx,
                                                               anyway_rgx_year))

        integrity_34 = re.compile(
            r'({0}年|{5}年)({8})(日)(?!{7})'.format(year_chinese_num_rgx,
                                                          # s = '去年是2019年21日（星期五）下午8点到2019年5月22日一起去吃饭
                                                          seg_trigger_rgx,
                                                          # s = '去年是二零一九年21日（星期五）下午8点到2019年5月22日一起去吃饭
                                                          period_time_rgx,
                                                          month_chinese_num_rgx,
                                                          hour_time_rgx,
                                                          year_arab_num_rgx,
                                                          month_arab_num_rgx,
                                                          time_type_rgx,
                                                          anyway_rgx_year))

        integrity_35 = re.compile(
            r'({0}年|{5}年)({8})(日)({2})({3}{4}|{6}{4})(?!{7})'.format(year_chinese_num_rgx,
                                                                          # s = '去年是2019年21日（星期五）下午8点到2019年5月22日上午八点一起去吃饭
                                                                          seg_trigger_rgx,
                                                                          # s = '去年是二零一九年21日（星期五）下午8点到2019年5月22日上午8点一起去吃饭
                                                                          period_time_rgx,
                                                                          month_chinese_num_rgx,
                                                                          hour_time_rgx,
                                                                          year_arab_num_rgx,
                                                                          month_arab_num_rgx,
                                                                          time_type_rgx,
                                                                          anyway_rgx_year))

        integrity_36 = re.compile(
            r'({3}月|{6}月)({8})(日)[(|（](.*?)[)|）]({2})(?!{7})'.format(year_chinese_num_rgx,
                                                                              # s = '去年是5月21日（星期五）下午8点到2019年5月22日（星期六）上午一起去吃饭
                                                                              seg_trigger_rgx,
                                                                              # s = '去年是五月21日（星期五）下午8点到2019年5月22日（星期六）上午一起去吃饭
                                                                              period_time_rgx,
                                                                              month_chinese_num_rgx,
                                                                              hour_time_rgx,
                                                                              year_arab_num_rgx,
                                                                              month_arab_num_rgx,
                                                                              time_type_rgx,
                                                                              anyway_rgx_day2))

        integrity_37 = re.compile(
            r'({3}月|{6}月)({8})(日)[(|（](.*?)[)|）]({3}{4}|{6}{4})(?!{7})'.format(year_chinese_num_rgx,
                                                                                    # s = '去年是5月21日（星期五）下午8点到2019年5月22日（星期六）8点一起去吃饭
                                                                                    seg_trigger_rgx,
                                                                                    # s = '去年是五月21日（星期五）下午8点到2019年5月22日（星期六）八点一起去吃饭
                                                                                    period_time_rgx,
                                                                                    month_chinese_num_rgx,
                                                                                    hour_time_rgx,
                                                                                    year_arab_num_rgx,
                                                                                    month_arab_num_rgx,
                                                                                    time_type_rgx,
                                                                                    anyway_rgx_day2))

        integrity_38 = re.compile(
            r'({3}月|{6}月)({8})(日)[(|（](.*?)[)|）](?!{7})'.format(year_chinese_num_rgx,
                                                                         # s = '去年是5月21日（星期五）下午8点到2019年5月22日（星期六）一起去吃饭
                                                                         seg_trigger_rgx,
                                                                         # s = '去年是五月21日（星期五）下午8点到2019年5月22日（星期六）一起去吃饭
                                                                         period_time_rgx,
                                                                         month_chinese_num_rgx,
                                                                         hour_time_rgx,
                                                                         year_arab_num_rgx,
                                                                         month_arab_num_rgx,
                                                                         time_type_rgx,
                                                                         anyway_rgx_day2))

        integrity_39 = re.compile(
            r'({3}月|{6}月)({8})(日)({3}{4}|{6}{4})(?!{7})'.format(year_chinese_num_rgx,
                                                                     # s = '去年是5月21日（星期五）下午8点到2019年5月22日8点一起去吃饭
                                                                     seg_trigger_rgx,
                                                                     # s = '去年是五月21日（星期五）下午8点到2019年5月22日八点一起去吃饭
                                                                     period_time_rgx,
                                                                     month_chinese_num_rgx,
                                                                     hour_time_rgx,
                                                                     year_arab_num_rgx,
                                                                     month_arab_num_rgx,
                                                                     time_type_rgx,
                                                                     anyway_rgx_day2))

        integrity_40 = re.compile(
            r'({3}月|{6}月)({8})(日)({2})(?!{7})'.format(year_chinese_num_rgx,
                                                               # s = '去年是5月21日（星期五）下午8点到2019年5月22日上午一起去吃饭
                                                               seg_trigger_rgx,
                                                               # s = '去年是五月21日（星期五）下午8点到2019年5月22日上午一起去吃饭
                                                               period_time_rgx,
                                                               month_chinese_num_rgx,
                                                               hour_time_rgx,
                                                               year_arab_num_rgx,
                                                               month_arab_num_rgx,
                                                               time_type_rgx,
                                                               anyway_rgx_day2))

        integrity_41 = re.compile(
            r'({3}月|{6}月)({8})(日)(?!{7})'.format(year_chinese_num_rgx,
                                                          # s = '去年是5月21日（星期五）下午8点到2019年5月22日一起去吃饭
                                                          seg_trigger_rgx,
                                                          # s = '去年是五月21日（星期五）下午8点到2019年5月22日一起去吃饭
                                                          period_time_rgx,
                                                          month_chinese_num_rgx,
                                                          hour_time_rgx,
                                                          year_arab_num_rgx,
                                                          month_arab_num_rgx,
                                                          time_type_rgx,
                                                          anyway_rgx_day2))

        integrity_42 = re.compile(
            r'({3}月|{6}月)({8})(日)({2})({3}{4}|{6}{4})(?!{7})'.format(year_chinese_num_rgx,
                                                                          # s = '去年是5月21日（星期五）下午8点到2019年5月22日上午8点一起去吃饭
                                                                          seg_trigger_rgx,
                                                                          # s = '去年是五月21日（星期五）下午8点到2019年5月22日上午8点一起去吃饭
                                                                          period_time_rgx,
                                                                          month_chinese_num_rgx,
                                                                          hour_time_rgx,
                                                                          year_arab_num_rgx,
                                                                          month_arab_num_rgx,
                                                                          time_type_rgx,
                                                                          anyway_rgx_day2))

        integrity_43 = re.compile(
            r'({0}日|{6}日)[(|（](.*?)[)|）]({2})(?!{7})'.format(year_chinese_num_rgx,
                                                                       # s = '去年是21日（星期五）下午8点到2019年5月22日（星期六）上午一起去吃饭
                                                                       seg_trigger_rgx,
                                                                       # s = '去年是二十一日（星期五）下午8点到2019年5月22日（星期六）上午一起去吃饭
                                                                       period_time_rgx,
                                                                       month_chinese_num_rgx,
                                                                       hour_time_rgx,
                                                                       year_arab_num_rgx,
                                                                       month_arab_num_rgx,
                                                                       time_type_rgx))

        integrity_44 = re.compile(
            r'({0}日|{6}日)[(|（](.*?)[)|）]({3}{4}|{6}{4})(?!{7})'.format(year_chinese_num_rgx,
                                                                             # s = '去年是21日（星期五）下午8点到2019年5月22日（星期六）8点一起去吃饭
                                                                             seg_trigger_rgx,
                                                                             # s = '去年是二十一日（星期五）下午8点到2019年5月22日（星期六）八点一起去吃饭
                                                                             period_time_rgx,
                                                                             month_chinese_num_rgx,
                                                                             hour_time_rgx,
                                                                             year_arab_num_rgx,
                                                                             month_arab_num_rgx,
                                                                             time_type_rgx))

        integrity_45 = re.compile(
            r'({0}日|{6}日)[(|（](.*?)[)|）](?!{7})'.format(year_chinese_num_rgx,
                                                                  # s = '去年是21日（星期五）下午8点到2019年5月22日（星期六）一起去吃饭
                                                                  seg_trigger_rgx,
                                                                  # s = '去年是二十一日（星期五）下午8点到2019年5月22日（星期六）一起去吃饭
                                                                  period_time_rgx,
                                                                  month_chinese_num_rgx,
                                                                  hour_time_rgx,
                                                                  year_arab_num_rgx,
                                                                  month_arab_num_rgx,
                                                                  time_type_rgx))

        integrity_46 = re.compile(
            r'({0}日|{6}日)({3}{4}|{6}{4})(?!{7})'.format(year_chinese_num_rgx,
                                                              # s = '去年是21日（星期五）下午8点到2019年5月22日8点一起去吃饭
                                                              seg_trigger_rgx,
                                                              # s = '去年是二十一日（星期五）下午8点到2019年5月22日八点一起去吃饭
                                                              period_time_rgx,
                                                              month_chinese_num_rgx,
                                                              hour_time_rgx,
                                                              year_arab_num_rgx,
                                                              month_arab_num_rgx,
                                                              time_type_rgx))

        integrity_47 = re.compile(
            r'({0}日|{6}日)({2})(?!{7})'.format(year_chinese_num_rgx,
                                                        # s = '去年是21日（星期五）下午8点到2019年5月22日上午一起去吃饭
                                                        seg_trigger_rgx,
                                                        # s = '去年是二十一日（星期五）下午8点到2019年5月22日上午一起去吃饭
                                                        period_time_rgx,
                                                        month_chinese_num_rgx,
                                                        hour_time_rgx,
                                                        year_arab_num_rgx,
                                                        month_arab_num_rgx,
                                                        time_type_rgx))

        integrity_48 = re.compile(
            r'({0}日|{6}日)({2})({3}{4}|{6}{4})(?!{7})'.format(year_chinese_num_rgx,
                                                                   # s = '去年是21日（星期五）下午8点到2019年5月22日上午8点一起去吃饭
                                                                   seg_trigger_rgx,
                                                                   # s = '去年是二十一日（星期五）下午8点到2019年5月22日上午八点一起去吃饭
                                                                   period_time_rgx,
                                                                   month_chinese_num_rgx,
                                                                   hour_time_rgx,
                                                                   year_arab_num_rgx,
                                                                   month_arab_num_rgx,
                                                                   time_type_rgx))

        integrity_49 = re.compile(
            r'({0}日|{6}日)(?!{7})'.format(year_chinese_num_rgx,
                                                   # s = '去年是21日（星期五）下午8点到2019年5月22日一起去吃饭
                                                   seg_trigger_rgx,
                                                   # s = '去年是二十一日（星期五）下午8点到2019年5月22日一起去吃饭
                                                   period_time_rgx,
                                                   month_chinese_num_rgx,
                                                   hour_time_rgx,
                                                   year_arab_num_rgx,
                                                   month_arab_num_rgx,
                                                   time_type_rgx))

        self.rpt_orderby_rgx = [integrity_1_0,integrity_1_1,integrity_1_2]
        self.tmp_orderby_rgx = [integrity_2,integrity_5,integrity_6,integrity_10,integrity_7,integrity_8,integrity_9,integrity_23,integrity_3,integrity_11,integrity_12,
                                integrity_16, integrity_13, integrity_14, integrity_15, integrity_24, integrity_4,
                                integrity_17, integrity_18, integrity_22, integrity_19, integrity_20,
                                integrity_21, integrity_25, integrity_50, integrity_51, integrity_55, integrity_52, integrity_53,
                                integrity_54, integrity_56,integrity_26, integrity_29, integrity_30, integrity_35,
                                integrity_31, integrity_32, integrity_33, integrity_34, integrity_27,
                                integrity_36, integrity_37, integrity_42, integrity_38, integrity_39, integrity_40,
                                integrity_41, integrity_28, integrity_43, integrity_44, integrity_48,
                                integrity_45, integrity_46, integrity_47, integrity_49]


    def get_date_chunk(self,s):

        time_chunk_list = []

        for i in range(0,len(self.rpt_orderby_rgx)):
            item_rgx = self.rpt_orderby_rgx[i].search(s)
            if item_rgx is not None:
                report_time_chunk_dict = {}
                report_time_chunk_dict['offset'] = [item_rgx.span()[0],item_rgx.span()[1]]
                report_time_chunk_dict['time_str'] = item_rgx.group(0)
                report_time_chunk_dict['type'] = 'RPT'
                time_chunk_list.append(report_time_chunk_dict)
                break
            else:
                pass

        for i in range(0,len(self.tmp_orderby_rgx)):
            item_rgx = self.tmp_orderby_rgx[i].search(s)
            if item_rgx is not None:
                event_time_chunk_dict = {}
                event_time_chunk_dict['offset'] = [item_rgx.span()[0], item_rgx.span()[1]]
                event_time_chunk_dict['time_str'] = item_rgx.group(0)
                event_time_chunk_dict['type'] = 'TMP'
                time_chunk_list.append(event_time_chunk_dict)
                #print(item_rgx.groups())
                #print(i)
                #print(self.tmp_orderby_rgx[i])
                break
            else:
                pass

        #print(time_chunk_list)

        return time_chunk_list


    def normalize_datetime(self,time_chunk_list):

        normalize_chunk = self.normalize_chunk

        if len(time_chunk_list) > 0:

            for time_chunk in time_chunk_list:

                time_str_list = []
                time_chunk_str = time_chunk['time_str']
                time_chunk_rgx = normalize_chunk.search(time_chunk_str)

                if time_chunk_rgx is not None:
                    time_str_list.append(time_chunk_rgx.group(1))
                    time_str_list.append(time_chunk_rgx.group(3))

                else:
                    time_str_list.append(time_chunk_str)

                time_chunk_list[time_chunk_list.index(time_chunk)]['time_str'] = time_str_list

            return time_chunk_list

        else:
            return time_chunk_list

    def parse_datetime(self,time_chunk_list, publishAt):

        arab_num = []
        for i in range(1, 32):
            num = str(i)
            arab_num.append(num)

        Chinese_num = self.Chinese_num

        rule = self.rule

        timeStamp = publishAt / 1000

        timeArray = time.localtime(timeStamp)

        otherStyleTime = time.strftime("%Y-%m-%d", timeArray)
        otherStyleTime_list = otherStyleTime.split('-')
        otherStyleTime_list[0] = otherStyleTime_list[0] + '年'
        otherStyleTime_list[1] = otherStyleTime_list[1] + '月'
        otherStyleTime_list[2] = otherStyleTime_list[2] + '日'

        time_single_list = []

        for time_chunk in time_chunk_list:
            for item in time_chunk['time_str']:
                time_single_list.append(item)

        for time_chunk in time_chunk_list:

            msgs = time_chunk['time_str']
            time_chunk['full_time_str'] = []
            time_chunk['time_stamp'] = []

            for msg in msgs:
                k = -1

                if msg is None or len(msg) == 0:
                    time_chunk['time_stamp'] = 0
                else:
                    m_1 = re.match(
                        r"([0-9零一二两三四五六七八九十]+年)?([0-9一二两三四五六七八九十]+月)?([0-9一二两三四五六七八九十]+[号日])?([上中下午晚早]+)?([0-9零一二两三四五六七八九十百]+[点:\.时])?([0-9零一二三四五六七八九十百]+分)?([0-9零一二三四五六七八九十百]+秒)?",
                        msg)
                    # print(m_1.group(0))
                    if m_1.group(0) is not None:
                        res_list = ['year', 'month', 'day']
                        res = {
                            "year": m_1.group(1),
                            "month": m_1.group(2),
                            "day": m_1.group(3),
                            # "hour": m_1.group(5) if m_1.group(5) is not None else '00',
                            # "minute": m_1.group(6) if m_1.group(6) is not None else '00',
                            # "second": m_1.group(7) if m_1.group(7) is not None else '00',
                        }
                        params = {}

                        for name in res_list:
                            k = k + 1

                            if res[name] is None:

                                i = time_single_list.index(msg)

                                while (True):
                                    if i >= 0:

                                        m_2 = re.search(rule[k], time_single_list[i])

                                        # if m_2 is not None:
                                        #     print(m_2.group(0))
                                        if m_2 is not None:
                                            res[name] = m_2.group(1)
                                            break
                                        i = i - 1

                                    else:
                                        res[name] = otherStyleTime_list[res_list.index(name)]
                                        break

                        time_str1 = res["year"] + res["month"] + res["day"]
                        year = re.findall(r"(.+?)年", time_str1)
                        month = re.findall(r"年(.+?)月", time_str1)
                        day = re.findall(r"月(.+?)日", time_str1)
                        # print(year)
                        # print(month)
                        # print(day)

                        if day[0] in Chinese_num:
                            day[0] = arab_num[Chinese_num.index(day[0])]

                        if month[0] in Chinese_num:
                            month[0] = arab_num[Chinese_num.index(month[0])]

                        try:
                            dateC = datetime.datetime(int(year[0]), int(month[0]), int(day[0]), 00, 00)
                            # print(dateC)
                            timestamp = int(time.mktime(dateC.timetuple()) * 1000)
                        except Exception as e:
                            dateC = 0
                            timestamp = 0
                            print(e)

                        time_chunk['time_stamp'].append(timestamp)
                        time_chunk['full_time_str'].append(year[0] + '年' + month[0] + '月' + day[0] + '日')

        if time_chunk_list == []:
            full_time_str = str(datetime.datetime.fromtimestamp(publishAt / 1000))

            time_chunk_list = [{'time_stamp': [publishAt], 'offset': [0,0], 'time_str': [''], 'full_time_str': [full_time_str], 'type': 'TMP'}]

        return time_chunk_list


if __name__ == '__main__':

    s = '全国工业和信息化工作会议17-18日上午在京召开'
    s = '我国高分辨率对地观测系统的高分五号和六号两颗卫星21日正式投入使用，标志着国家高分辨率对地观测系统重大专项(高分专项)打造的高空间分辨率、高时间分辨率、高光谱分辨率的天基对地观测能力中最有应用特色的高光谱能力的形成。'
    date_chunk_handle = Date_chunk_handle()
    time_chunk_list = date_chunk_handle.get_date_chunk(s)

    normalize_list = date_chunk_handle.normalize_datetime(time_chunk_list)
    print(normalize_list)
    publishAt = 1555862400000
    time_stamp_list = date_chunk_handle.parse_datetime(normalize_list, publishAt)
    print(time_stamp_list)
    print("******************************************************************************")

    # with io.open('./2019-04-04_events.txt','r',encoding='utf-8') as f:
    #     while True:
    #         line = f.readline()
    #
    #         if len(line) > 0:
    #             json_data = json.loads(line)
    #             str1 = json_data["event_discription"]
    #             print(str1)
    #             time_chunk_list = date_chunk_handle.get_date_chunk(str1)
    #             normalize_list = date_chunk_handle.normalize_datetime(time_chunk_list)
    #             print(normalize_list)
    #             publishAt = 1555862400000
    #             time_stamp_list = date_chunk_handle.parse_datetime(normalize_list, publishAt)
    #             print(time_stamp_list)
    #             print("******************************************************************************")
    #
    #         else:
    #             break

        # print("End.")
