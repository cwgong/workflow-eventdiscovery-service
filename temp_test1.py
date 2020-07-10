# -*- coding: utf-8 -*-
import os
import json
import codecs

def get_origin_cluster_result(end_time):
    c = 0
    origin_cluster_result = []
    if not os.path.exists('logs/origin_cluster.txt'):
        return origin_cluster_result
    for line in codecs.open('logs/origin_cluster.txt', encoding='utf-8'):
        try:
            line = json.loads(line)
        except:
            continue
        info_ids = line['info_ids']
        length = len(info_ids)
        
        publish_time = line['publish_time']
        if length > 1:
            c += 1
        # 簇大小为1：去掉时间跨度大于一天的簇
        if length == 1:
            if end_time - publish_time > int(2*24*60*60*1000):
                continue
        # 簇大小大于1：去掉时间跨度大于三天的簇
        else:
            if end_time - publish_time > int(3*24*60*60*1000):
                continue
        origin_cluster_result.append(line)
    
    print(len(origin_cluster_result))
    print(c)
    return origin_cluster_result

end_time = 1541501963999
get_origin_cluster_result(end_time)