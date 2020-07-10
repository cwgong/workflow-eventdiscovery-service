# -*- encoding:utf8 -*-
import io
import os
import time_utils
import json
import requests
import logging.config
import codecs

logging.config.fileConfig("logging.conf")
logger = logging.getLogger('main')

def get_check_point():
    '''
    获取上一次更新聚类的时间点；
    如果没有这个时间点，则将时间点设置为三天前，启动第一次聚类；
    '''
    with io.open('config/checkpoint', 'r', encoding='utf-8') as f:
        _check_point_time = f.read()
    if not _check_point_time.strip():
        print("set check_point_time to three days ago")
        #_check_point_time = time_utils.three_days_ago_milli_time()
        _check_point_time = time_utils.n_days_ago_milli_time(1)
    return int(_check_point_time)

def save_check_point(_check_point_time):
    '''
    保存这次更新聚类的时间点
    '''
    with io.open('config/checkpoint', 'w', encoding='UTF-8') as f:
        f.write(str(_check_point_time))

def strip_tags(html):
    import re
    dr = re.compile(r'<[^>.*]+>', re.S)
    dd = dr.sub('', html)
    return dd

def split_sentence(sen):
    nlp_url = 'http://hanlp-rough-service:31001/hanlp/segment/rough'
    try:
        cut_sen = dict()
        cut_sen['content'] = sen
        data = json.dumps(cut_sen).encode("UTF-8")
        cut_response = requests.post(nlp_url, data=data, headers={'Connection':'close'})
        cut_response_json = cut_response.json()
        return cut_response_json['data']
    except Exception as e:
        logger.exception("Exception: {}".format(e))
        return []

def load_data_from_api(start_time, end_time, data_file):

    list_url = 'http://information-doc-service:31001/information/search?'
    detail_url = 'http://information-doc-service:31001/information/detail/'
    ids_count = 0
    try:
        cp = 1
        while True:
            params = dict()
            params["cp"] = cp
            params["ps"] = 1000
            params["timeField"] = 'publishAt'
            params["startAt"] = start_time
            params["endAt"] = end_time
            params["directions"] = 'ASC'

            r = requests.get(list_url, params)
            result_json = r.json()

            if len(result_json['data']) == 0:
                break
            
            with io.open(data_file, 'a', encoding='utf-8') as f:
                for item in result_json['data']:
                    try:
                        detail_result = requests.get(detail_url + item['id'])
                        detail_json = detail_result.json()
                        title = detail_json['data']['title']
                    except Exception as e:
                        continue
                    logger.info(item['id'] + ' ' + title)
                    ids_count += 1
                    f.write(json.dumps(detail_json['data'], ensure_ascii=False) + "\n")
            cp += 1
    except Exception as e:
        logger.exception("Exception: {}".format(e))
        
    logger.info("all_ids: {}".format(ids_count))


def get_extradata_from_api(start_time, end_time, original_data_file, extradata_file):

    list_url = 'http://information-doc-service:31001/information/search?'
    detail_url = 'http://information-doc-service:31001/information/detail/'
    
    logger.info("get_extradata_from_api original_data_file_exist: {}".format(os.path.exists(original_data_file)))
    if not os.path.exists(original_data_file):
        ids_count = 0
        f = codecs.open(original_data_file, 'w', encoding='utf-8')
        try:
            cp = 1
            while True:
                params = dict()
                params["cp"] = cp
                params["ps"] = 1000
                params["timeField"] = 'publishAt'
                params["startAt"] = start_time
                params["endAt"] = end_time
    
                r = requests.get(list_url, params)
                result_json = r.json()
    
                if len(result_json['data']) == 0:
                    break
                
                for item in result_json['data']:
                    try:
                        detail_result = requests.get(detail_url + item['id'])
                        detail_json = detail_result.json()
                        title = detail_json['data']['title']
                    except Exception as e:
                        continue
                    ids_count += 1
                    logger.info(item['id'] + ' ' + title)
                    f.write(json.dumps(detail_json['data'], ensure_ascii=False) + "\n")
                cp += 1
        except Exception as e:
            logger.exception("Exception: {}".format(e))
        logger.info("all_ids: {}".format(ids_count))
        f.close()
        return original_data_file, []
    
    else:
        old_ids = []
        with io.open(original_data_file, 'r', encoding='utf-8') as f:
            while True:
                line = f.readline()
                if len(line) > 0:
                    try:
                        json_data = json.loads(line)
                    except:
                        logger.info("line error: {}".format(line))
                        continue
                    old_ids.append(json_data['id'])
                else:
                    break
            
        logger.info("old_ids: {}".format(len(old_ids)))
        
        new_file_data = []
        extra_ids_count = 0
        ids_count = 0
        # 每次覆盖掉 extradata_file
        f = codecs.open(extradata_file, 'w', encoding='utf-8')
        try:
            cp = 1
            while True:
                params = dict()
                params["cp"] = cp
                params["ps"] = 1000
                params["timeField"] = 'publishAt'
                params["startAt"] = start_time
                params["endAt"] = end_time
    
                r = requests.get(list_url, params)
                result_json = r.json()
    
                if len(result_json['data']) == 0:
                    break
                
                for item in result_json['data']:
                    try:
                        detail_result = requests.get(detail_url + item['id'])
                        detail_json = detail_result.json()
                        title = detail_json['data']['title']
                    except Exception as e:
                        continue
                    if item['id'] not in old_ids:
                        logger.info(item['id'] + ' ' + title)
                        f.write(json.dumps(detail_json['data'], ensure_ascii=False) + "\n")
                        extra_ids_count += 1
                    new_file_data.append(json.dumps(detail_json['data'], ensure_ascii=False))
                    ids_count += 1
                cp += 1
        except Exception as e:
            logger.exception("Exception: {}".format(e))
        f.close()
        logger.info("all_ids: {}".format(ids_count))
        logger.info("extra_ids: {}".format(extra_ids_count))
        return extradata_file, new_file_data
    
def update_original_data_file(new_file_data, original_data_file):
    
    count = 0
    if len(new_file_data) == 0:
        logger.info("first time not update original_data_file: {}".format(count))
        return

    # 每次覆盖掉 original_data_file
    f = codecs.open(original_data_file, 'w', encoding='utf-8')
    for item in new_file_data:
        f.write(item+'\n')
        count += 1
    f.close()
    logger.info("update_original_data_file ids: {}".format(count))
