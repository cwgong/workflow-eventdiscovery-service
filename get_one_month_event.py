# -*- encoding:utf8 -*-
import functools
import logging.config
import time
import os
os.environ["KMP_DUPLICATE_LIB_OK"]="TRUE" # 解决 mac os torch 报错 libomp
import schedule
from threading import Timer
import io
import json
import codecs

import cluster
import cluster2
import load_text_data
import save_cluster_result
import time_utils
import load_cluster_and_process

import timeout_decorator

logging.config.fileConfig("logging.conf")
logger = logging.getLogger('main')

def get_standard_time(time_stamp):
    
    timeArray = time.localtime(time_stamp/1000)
    otherStyleTime = time.strftime("%Y年%m月%d日", timeArray)
    return otherStyleTime

def processing(start_time, end_time):
    
    dir_path = './data1/'
    
    day = get_standard_time(end_time)
    logger.info("day processing... : {}".format(day))
    
    logger.info("load text data start_time: {}".format(start_time))
    logger.info("load text data end_time: {}".format(end_time))
    
    data_file = dir_path + day +'.txt'
    data_file_ = dir_path + day +'_.txt'
    cluster_result_file = dir_path + day +'_cluster_result.txt'
    cluster_triple_file = dir_path + day +'_cluster_triple.txt'
    triple_cluster_file = dir_path + day +'_triple_cluster.txt'
    
    load_text_data.load_data_from_api(start_time, end_time, data_file)
    logger.info("load text data file path...: {}".format(data_file))
    
    data_file_ = cluster2.data_event_process(data_file, data_file_)
    
    ner_content_data, word_content_data, text_data, word_title_data, raw_data = cluster2.fetch_data(data_file_)
    
    length_data = len(raw_data)
    logger.info('cluster corpus size: ' + str(length_data))   
    
    # 太少的数据不做聚类
    if length_data < 100:
        logger.info("corpus size is too small only update end_time: {}".format(end_time))

    origin_cluster_result = []
    
    cluster_result = cluster2.cluster(origin_cluster_result, ner_content_data, word_content_data, text_data, word_title_data, raw_data)  
    
    with io.open(cluster_result_file, 'w', encoding='utf-8') as f1:
        for x in cluster_result:
            f1.write(json.dumps(x, ensure_ascii=False) + "\n")

    all_cluster_event_infos = load_cluster_and_process.load_cluster_info_process(cluster_result_file, cluster_triple_file, hot_filter = 0)
    
    load_cluster_and_process.all_cluster_event_infos_process(all_cluster_event_infos, triple_cluster_file)
    

def job():
    
    
    start_time = 1557936000000 # 2019/5/5 7:00
    
    current_time = int(round(time.time() * 1000)) # 当前的时间
    
    gap_time = int(24*60*60*1000) 

    
    epoch = int((current_time - start_time)/gap_time)

    for i in range(0, epoch):
        
        end_time = start_time + gap_time
        processing(start_time, end_time)
        start_time = end_time
        logger.info('i: ' + str(i) + ' in epoch: ' + str(epoch) + ' over...')
    

    
if __name__ == '__main__':
    
    job()
    
