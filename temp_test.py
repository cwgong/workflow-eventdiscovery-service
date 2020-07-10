# -*- coding: utf-8 -*-

a = [1,2]
print(a[3:])
import requests
import json

def load_data_from_api():
    '''
    获取新增的数据
    '''
    start_time = 1539878400000 # 10.19.00
    end_time = start_time+(3*24*60*60*1000) # 10.22.00 当天的新闻
    
    start_time = 1540483200000 # 10.26.00
    end_time = start_time+(3*24*60*60*1000) # 10.29.00 当天的新闻
    
    start_time = 1540915200000
    end_time = int(start_time+(0.9*24*60*60*1000)) # 10.29.00 当天的新闻
    c = 0
    list_url = 'http://information-doc-service:31001/information/search?'
    detail_url = 'http://information-doc-service:31001/information/detail/'
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
                detail_result = requests.get(detail_url + item['id'])
                detail_json = detail_result.json()

                c +=1
                print(c)
            cp += 1
            #print(c)
    except Exception as e:
        print("Exception: {}".format(e))
        
    print(c)
    
#load_data_from_api()


top_term = [1,2,3,4,5,5,5]
title_words = [2,3,6,5]
size = len(set(top_term) & set(title_words))
print(size)
print(set(top_term) & set(title_words))


print(list(set(top_term)))



cluster_result_ = []
cluster_result = [{'id': 1}, {'id': 2},{'id': 3},{'id': 4},{'id': 5},{'id': 6},{'id': 9}]

for i in range(0, len(cluster_result)):
    # 各自成簇大于一定阈值，再进行归并
    if cluster_result[i]['id'] > 4:
        condition = 0
        for j in range(0, len(cluster_result_ )):
            if cluster_result[i]['id'] - cluster_result_[j]['id']  == 8:
                cluster_result_[j]['id'] = 1000

                condition += 1
                break
        if condition == 0:
            cluster_result_.append(cluster_result[i])
    else:
        cluster_result_.append(cluster_result[i])
        
print(cluster_result_)