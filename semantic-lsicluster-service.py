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

import timeout_decorator

logging.config.fileConfig("logging.conf")
logger = logging.getLogger('main')

# 跑实时数据，由于是按 publishAt 字段跑数据，但 publishAt 的获取即 createAt 
# 可能比 当前时刻晚，即下一次增量时才能获取到 puvlishAt，需要处理该部分
# 实时流不需要 load_text_data.save_check_point(end_time) 和 start_time = load_text_data.get_check_point()
# 但需要 get_origin_cluster_result(origin_cluster_file_path, end_time, n_reserve_days_for_1size_cluster, n_reserve_days)
# 这里的 end_time 指的是当前时间
# 防止 超过限定时间 卡住 而不运行
@timeout_decorator.timeout(60*60*2, use_signals=False)
def cluster_text_job():
    logger.info('cluster_text_job() start...')
    
    # 政府资讯的 pulish time 是 0 点
    compare_time_gap = 1.5
    start_time = time_utils.n_days_ago_milli_time(compare_time_gap)
    end_time = time_utils.current_milli_time()
    logger.info("load text data start_time: {}".format(start_time))
    logger.info("load text data end_time: {}".format(end_time))
    
    original_data_file = 'logs/original_data.txt'
    extradata_file = 'logs/extra_data.txt'
    
    # 由于是按着 publish time 增量，需要自己进行比对
    data_file, new_file_data = load_text_data.get_extradata_from_api(start_time, end_time, original_data_file, extradata_file)
    logger.info("load text data file path...: {}".format(data_file))
    
    # 两个版本
    #ner_content_data, raw_data = cluster.fetch_data(data_file)
    ner_content_data, word_content_data, text_data, word_title_data, raw_data = cluster2.fetch_data(data_file)
    
    length_data = len(raw_data)
    logger.info('cluster corpus size: ' + str(length_data))   
    # 太少的数据不做聚类
    if length_data < 100:
        logger.info("corpus size is too small only update end_time: {}".format(end_time))
        return
    
    # 覆盖掉 original_data_file
    load_text_data.update_original_data_file(new_file_data, original_data_file)    
    new_file_data = None
    
    # 取上一次聚类结果（增量聚类）
    origin_cluster_file_path = 'logs/origin_cluster.txt'
    n_reserve_days_for_1size_cluster = 1
    n_reserve_days = 1
    # 两个版本 同上
    #origin_cluster_result = cluster.get_origin_cluster_result(origin_cluster_file_path, end_time, n_reserve_days_for_1size_cluster, n_reserve_days)
    origin_cluster_result = cluster2.get_origin_cluster_result(origin_cluster_file_path, end_time, n_reserve_days_for_1size_cluster, n_reserve_days)
    
    # 开始聚类
    # 两个版本 同上
    #cluster_result = cluster.cluster(origin_cluster_result, ner_content_data, raw_data)
    cluster_result = cluster2.cluster(origin_cluster_result, ner_content_data, word_content_data, text_data,word_title_data, raw_data)
    
    # 在本地此次保存更新后的聚类结果（如只保留近 1 天，删掉之前的时间簇，目的是参与下一次聚类，作为下一次
    # 增量聚类的基数，即考虑近 1 天的事件进行合并）
    cluster_result, cluster_already_merged = save_cluster_result.cluster_result_futher_merge(cluster_result, origin_cluster_file_path)
    save_cluster_result.dele_already_merged_cluster(cluster_already_merged)
    save_cluster_result.save_cluster_result(cluster_result, 1)
    
    logger.info('cluster_text_job() end...')
    
    
# 增量跑历史数据
def history_cluster_text_job():
    logger.info('history_cluster_text_job() start...')
    
    start_time = 1540915200000 # 10.31.00
    end_time = start_time+int((0.01*24*60*60*1000)) 
    current_time = int(round(time.time() * 1000)) # 当前的时间
    
    gap_time = int((4)*60*60*1000) # 4h
    store = 1
    
    epoch = int((current_time - end_time)/gap_time) + 1

    for i in range(0, epoch):
        
        if i == 0:
            start_time = start_time 
            end_time = end_time 
        else:
            start_time = load_text_data.get_check_point()
            end_time = start_time + (store * gap_time)
        
        logger.info("load text data start_time: {}".format(start_time))
        logger.info("load text data end_time: {}".format(end_time))
        
        # 取 爬取的资讯数据
        data_file = 'logs/' + time_utils.timestamp_to_date(end_time) + '.txt'
        load_text_data.load_data_from_api(start_time, end_time, data_file)
        
        ner_content_data, raw_data = cluster.fetch_data(data_file)
        length_data = len(raw_data)
        logger.info('cluster corpus size: ' + str(length_data))        
        # 太少的数据不做聚类
        if length_data < 100:
            store += 1
            continue
        
        # 取上一次聚类结果（增量聚类）
        origin_cluster_file_path = 'logs/origin_cluster.txt'
        n_reserve_days_for_1size_cluster = 1
        n_reserve_days = 1
        origin_cluster_result = cluster.get_origin_cluster_result(origin_cluster_file_path, end_time, n_reserve_days_for_1size_cluster, n_reserve_days)

        # 开始聚类
        cluster_result = cluster.cluster(origin_cluster_result, ner_content_data, raw_data)
    
        # 在本地此次保存更新后的聚类结果（如只保留近 1 天，删掉之前的时间簇，目的是参与下一次聚类，作为下一次
        # 增量聚类的基数，即考虑近 1 天的事件进行合并）
        cluster_result, cluster_already_merged = save_cluster_result.cluster_result_futher_merge(cluster_result, origin_cluster_file_path)
        save_cluster_result.dele_already_merged_cluster(cluster_already_merged)
        save_cluster_result.save_cluster_result(cluster_result, 3)
        
        # 最后再更新时间，以防止失败
        load_text_data.save_check_point(end_time)
        
        store = 1
        logger.info('i: ' + str(i) + ' in epoch: ' + str(epoch) )
    
    logger.info('history_cluster_text_job() end !')

def excute_timing(): 
    
    global t
    
    try:
        cluster_text_job()
    except Exception as e:
        logging.exception(e) 
        logger.info('Time Out')
        
    time_gap = int((1)*60*60*1000) # 间隔 1 小时（由于执行时间较长，可能为45分钟左右）
    t = Timer(time_gap/1000, excute_timing)
    t.start()
    
if __name__ == '__main__':
    
    '''
    try:
        logger.info('Timer start...')
        time_gap = int((1/3600)*60*60*1000) # 首次间隔 1 分钟（由于执行时间较长，可能为45分钟左右）
        t = Timer(time_gap/1000, excute_timing)
        t.start()
    except Exception as e:
        logging.exception(e) 

    
    #history_cluster_text_job()
    '''
    compare_time_gap = 1.5
    start_time = 1553097600000
    end_time = 1553270400000
    start_time = 1552320000000 # 3.12
    end_time = 1552442400000 #3.13 10
    logger.info("load text data start_time: {}".format(start_time))
    logger.info("load text data end_time: {}".format(end_time))
    
    original_data_file = 'logs/original_data.txt'
    extradata_file = 'logs/extra_data.txt'
    data_file_ = 'logs1/data_now.txt'
    
    # 由于是按着 publish time 增量，需要自己进行比对
    #data_file, new_file_data = load_text_data.get_extradata_from_api(start_time, end_time, original_data_file, extradata_file)
    #logger.info("load text data file path...: {}".format(data_file))
    
    data_file_ = cluster2.data_event_process(original_data_file, data_file_)
    # 两个版本
    #ner_content_data, raw_data = cluster.fetch_data(data_file)
    ner_content_data, word_content_data, text_data, word_title_data, raw_data = cluster2.fetch_data(data_file_)
    
    length_data = len(raw_data)
    logger.info('cluster corpus size: ' + str(length_data))   
    # 太少的数据不做聚类
    if length_data < 100:
        logger.info("corpus size is too small only update end_time: {}".format(end_time))

    
    # 覆盖掉 original_data_file
    #load_text_data.update_original_data_file(new_file_data, original_data_file)    
    #new_file_data = None
    
    # 取上一次聚类结果（增量聚类）
    origin_cluster_file_path = 'logs/origin_cluster.txt'
    n_reserve_days_for_1size_cluster = 1
    n_reserve_days = 1
    # 两个版本 同上
    #origin_cluster_result = cluster.get_origin_cluster_result(origin_cluster_file_path, end_time, n_reserve_days_for_1size_cluster, n_reserve_days)
    origin_cluster_result = cluster2.get_origin_cluster_result(origin_cluster_file_path, end_time, n_reserve_days_for_1size_cluster, n_reserve_days)
    
    # 开始聚类
    # 两个版本 同上
    #cluster_result = cluster.cluster(origin_cluster_result, ner_content_data, raw_data)
    cluster_result = cluster2.cluster(origin_cluster_result, ner_content_data, word_content_data, text_data, word_title_data, raw_data)  
    
    with io.open('logs1/cluster_result.txt', 'w', encoding='utf-8') as f1:
        for x in cluster_result:
            f1.write(json.dumps(x, ensure_ascii=False) + "\n")
        
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
