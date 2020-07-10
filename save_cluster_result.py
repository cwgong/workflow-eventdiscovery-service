# -*- encoding:utf8 -*-

import json
import logging.config
import requests
import codecs
import cluster

logging.config.fileConfig("logging.conf")
logger = logging.getLogger('main')

def get_artificial_created_status(ids):
    logger.info("get_artificial_created_ids:{}".format(ids))
    status = []
    url = 'http://information-doc-service:31001/cluster/search'
    params = dict()
    params["ids"] = ids
    try:
        r = requests.get(url, params)
        result_json = r.json()
        
        for i in range(0, len(ids)):
            c = 0
            for item in result_json['data']['list']:
                if item['id'] == ids[i]:
                    status.append(item['status'])
                    c += 1
                    break
            if c == 0:
                status.append('none')
            
    except Exception as e:
        logger.info('get_artificial_created_status failed ids:' + str(ids))
        return status

    logger.info("get_artificial_created_status:{}".format(status))
    return status

# 机器聚类日志
def save_cluster_log(cluster_result):
    cluster_log_url = 'http://information-doc-service:31001/cluster/log'
    post_data = []
    for item in cluster_result:
        cluster_log = dict()
        cluster_log['batchId'] = '热点事件'
        cluster_log['clusterId'] = item['id']
        cluster_log['hot'] = len(item['info_ids'])
        cluster_log['id'] = item['id']
        cluster_log['infoIds'] = item['info_ids']
        cluster_log['keywords'] = item['keywords']
        #logger.info(cluster_log)
        post_data.append(cluster_log)
    data = json.dumps(post_data).encode("UTF-8")
    requests.post(cluster_log_url, data=data)
    logger.info('save_cluster_log finished! ' + str(len(post_data)))

# information-doc 是 mongoDB
def save_cluster(cluster_result):
    logger.info('save_cluster')
    cluster_url = 'http://information-doc-service:31001/cluster/update'
    post_data = []
    for item in cluster_result:
        cluster_info = dict()
        cluster_info['clusterType'] = '热点事件'
        cluster_info['hot'] = len(item['info_ids'])
        cluster_info['id'] = item['id']
        cluster_info['keywords'] = item['keywords']
        cluster_info['publishAt'] = item['publish_time']
        cluster_info['title'] = item['title']
        #logger.info(cluster_info)
        post_data.append(cluster_info)
    data = json.dumps(post_data).encode("UTF-8")
    requests.post(cluster_url, data=data)
    logger.info('save_cluster finished! ' + str(len(post_data)))

# machine-cluster-operator 事件资讯流
def save_cluster_info(cluster_result):
    cluster_url = 'http://machine-cluster-operator:31001/cluster'
    post_data = []
    for item in cluster_result:
        cluster_info = dict()
        cluster_info['clusterType'] = '热点事件'
        cluster_info['hot'] = len(item['info_ids'])
        cluster_info['clusterId'] = item['id']
        cluster_info['keywords'] = item['keywords']
        cluster_info['infoIds'] = item['info_ids']
        #logger.info(cluster_info)
        post_data.append(cluster_info)
    data = json.dumps(post_data).encode("UTF-8")
    requests.post(cluster_url, data=data)
    logger.info('save_cluster_info finished! ' + str(len(post_data)))
    
def dele_cluster(cluster_result):
    logger.info('dele_cluster')
    cluster_url = 'http://information-doc-service:31001/cluster/update'
    post_data = []
    for item in cluster_result:
        cluster_info = dict()
        cluster_info['clusterType'] = '热点事件'
        cluster_info['hot'] = 0
        cluster_info['id'] = item['id']
        cluster_info['keywords'] = item['keywords']
        cluster_info['publishAt'] = item['publish_time']
        cluster_info['title'] = item['title']
        cluster_info['delFlag'] = 1
        #logger.info(cluster_info)
        post_data.append(cluster_info)
    data = json.dumps(post_data).encode("UTF-8")
    requests.post(cluster_url, data=data)
    logger.info('del_cluster finished! ' + str(len(post_data)))

def get_keywords_from_merged_cluster(words, words_):
    
    x = {}
    all_words = words + words_
    for title_words in all_words:
        for word in title_words:
            if word not in x.keys():
                x[word] = 1
            else:
                x[word] += 1 

    x_ = sorted(x.items(), key=lambda d:d[1], reverse = True)
    title_keywords = [word[0] for word in x_][0:5]
    # 不应该用 dict，打印出来会没有顺序
    title_keywords_dic = {}
    for word, count in x_:
        title_keywords_dic[word] = count
    return title_keywords, title_keywords_dic

def title_choose_from_merged_cluster(titles, titles_, titlewords, titlewords_ ,publishtimes, publishtimes_, keywords):
    a = titles + titles_
    b = publishtimes + publishtimes_
    c = titlewords + titlewords_
    m = {}
    x = []
    for i in range(0,len(b)):
        x.append((a[i], b[i]))
        m[a[i]] = c[i]
    x_ = sorted(x, key=lambda d:d[1], reverse = True)
    x__ = [word[0] for word in x_][0:3]
    
    title_ = ''
    max_size = 0
    for title in x__:
        size = len(set(keywords) & set(m[title]))
        if size >= max_size:
            max_size = size
            title_ = title
    
    return title_

def cluster_result_futher_merge_condition(title_keywords, title_keywords_, content_keywords, content_keywords_):
    
    if len(set(title_keywords) & set(title_keywords_)) >= int(3/5 * len(title_keywords)):
        logger.info("futher_merge_condition_type is:{}".format(1))
        return 1
    if len(set(content_keywords) & set(content_keywords_)) >= int(4/5 * len(content_keywords)):
        logger.info("futher_merge_condition_type is:{}".format(2))
        return 1
    if len(set(title_keywords) & set(title_keywords_)) >= int(2/5 * len(title_keywords)):
        if len(set(content_keywords) & set(content_keywords_)) >= int(1/2 * len(content_keywords)):
            logger.info("futher_merge_condition_type is:{}".format(3))
            return 1
    if len(set(title_keywords) & set(title_keywords_)) >= int(1/5 * len(title_keywords)):
        if len(set(content_keywords) & set(content_keywords_)) >= int(3/5 * len(content_keywords)):
            logger.info("futher_merge_condition_type is:{}".format(4))
            return 1
    return 0
    
def cluster_result_futher_merge(cluster_result, origin_cluster_file_path):
    
    logger.info("cluster_result_futher_merge_by_keywords:{}".format(len(cluster_result)))
    cluster_result_ = []
    cluster_already_merged = []
    for i in range(0, len(cluster_result)):
        # 各自成簇大于一定阈值，再进行归并
        if len(cluster_result[i]['info_ids']) > 3:
            condition = 0
            for j in range(0, len(cluster_result_ )):
                if len(cluster_result_[j]['info_ids']) > 3:
                    if cluster_result_futher_merge_condition(cluster_result[i]['keywords'], cluster_result_[j]['keywords'], cluster_result[i]['content_keywords'], cluster_result_[j]['content_keywords']) == 1:
                        
                        logger.info("before merged cluster_result_[j] id:{}".format(cluster_result_[j]['id']))
                        logger.info("before merged cluster_result_[j] info_ids:{}".format(cluster_result_[j]['info_ids']))
                        logger.info("before merged cluster_result_[j] keywords:{}".format(cluster_result_[j]['keywords']))
                        logger.info("before merged cluster_result_[j] title_keywords_dic:{}".format(cluster_result_[j]['title_keywords_dic']))
                        logger.info("before merged cluster_result_[j] title:{}".format(cluster_result_[j]['title']))
                        logger.info("before merged cluster_result_[j] all_titles:{}".format(cluster_result_[j]['all_titles']))
                        logger.info("before merged cluster_result_[j] content_keywords:{}".format(cluster_result_[j]['content_keywords']))
                        
                        logger.info("before merged cluster_result[i] id:{}".format(cluster_result[i]['id']))
                        logger.info("before merged cluster_result[i] info_ids:{}".format(cluster_result[i]['info_ids']))
                        logger.info("before merged cluster_result[i] keywords:{}".format(cluster_result[i]['keywords']))
                        logger.info("before merged cluster_result[i] title_keywords_dic:{}".format(cluster_result[i]['title_keywords_dic']))
                        logger.info("before merged cluster_result[i] title:{}".format(cluster_result[i]['title']))
                        logger.info("before merged cluster_result[i] all_titles:{}".format(cluster_result[i]['all_titles']))
                        logger.info("before merged cluster_result[i] content_keywords:{}".format(cluster_result[i]['content_keywords']))
                        
                        # 由于会出现人工创建的事件，不能让其已创建的被合并
                        # 正常是 i 合并到 j 中
                        i_id = cluster_result[i]['id']
                        j_id = cluster_result_[j]['id']
                        ids = [i_id, j_id]
                        status = get_artificial_created_status(ids)
                        # 除 id 外，都按正常顺序合并
                        # 如果 j 合并到 i 中，只更换簇 id
                        if status == ['1','0']:
                            logger.info("brfore merge artificial created id cluster_result_[j]['id']:{}".format(cluster_result_[j]['id']))
                            cluster_result_[j]['id'] = i_id
                            logger.info("after merge artificial created id cluster_result_[j]['id']:{}".format(cluster_result_[j]['id']))
                        # 如果都已被创建了事件，跳出循环，i 与 j 都不合并
                        if status == ['1','1']:
                            break
                                           
                        cluster_result_[j]['info_ids'] = cluster_result_[j]['info_ids'] + cluster_result[i]['info_ids']
                        cluster_result_[j]['info_ids_to_data'] = cluster_result_[j]['info_ids_to_data'] + cluster_result[i]['info_ids_to_data']
                        cluster_result_[j]['publish_time'] = max(cluster_result_[j]['publish_time'], cluster_result[i]['publish_time'])
                        keywords, title_keywords_dic = get_keywords_from_merged_cluster(cluster_result[i]['all_title_words'], cluster_result_[j]['all_title_words'])
                        cluster_result_[j]['keywords'] = keywords
                        cluster_result_[j]['title_keywords_dic'] = title_keywords_dic 
                                       
                        all_titlewords_in_cluster = cluster_result_[j]['all_title_words'] + cluster_result[i]['all_title_words']
                        all_titles_in_cluster = cluster_result_[j]['all_titles'] + cluster_result[i]['all_titles']
                        # 根据标题关键词选取标题
                        title = ''
                        max_size = 0
                        for k in range(0, len(all_titlewords_in_cluster)):
                            size = len(set(keywords) & set(all_titlewords_in_cluster[k]))
                            if  size > max_size:
                                max_size = size
                                title = all_titles_in_cluster[k]  
                                       
                                       
                        cluster_result_[j]['title'] = title
                                       
                        cluster_result_[j]['all_titles']  = all_titles_in_cluster
                        cluster_result_[j]['all_title_words'] = all_titlewords_in_cluster
                        cluster_result_[j]['all_publishtime'] = cluster_result_[j]['all_publishtime'] + cluster_result[i]['all_publishtime']
                        cluster_result_[j]['min_publishtime'] = min(cluster_result_[j]['all_publishtime'] + cluster_result[i]['all_publishtime'])
                        cluster_result_[j]['max_publishtime'] = max(cluster_result_[j]['all_publishtime'] + cluster_result[i]['all_publishtime'])
                        
                        condition += 1
                        
                        logger.info("after merged id:{}".format(cluster_result_[j]['id']))
                        logger.info("after merged info_ids:{}".format(cluster_result_[j]['info_ids']))
                        logger.info("after merged keywords:{}".format(keywords))
                        logger.info("after merged title_keywords_dic:{}".format(title_keywords_dic))
                        logger.info("after merged title:{}".format(title))
                        logger.info("after merged all_titles:{}".format(cluster_result_[j]['all_titles']))
                        
                        # 将已合并的簇 delFlag = 1
                        if status == ['1','0']:
                            cluster_result[i]['id'] = j_id
                            cluster_already_merged.append(cluster_result[i])
                        else:
                            cluster_already_merged.append(cluster_result[i])
                            
                        logger.info("already merged id:{}".format(cluster_result[i]['id']))
                        break
                    
            if condition == 0:
                cluster_result_.append(cluster_result[i])
        else:
            cluster_result_.append(cluster_result[i])
    
    fout = codecs.open(origin_cluster_file_path, 'w', encoding='utf-8')
    for item in cluster_result_:
        strObj = json.dumps(item, ensure_ascii=False)
        fout.write(strObj+'\n')
    fout.close()
    
    return cluster_result_, cluster_already_merged

def dele_already_merged_cluster(cluster_already_merged):
    
    dele_cluster(cluster_already_merged)

def save_cluster_result(cluster_result, cluster_size_threshold):
    
    logger.info('save_cluster_result start...')
    logger.info('cluster_size_threshold: ' + str(cluster_size_threshold))
    
    cluster_result_ = []
    for item in cluster_result:
        score = item['score']
        title = item['title']
        keywords = item['keywords']
        cluster_id = item['id']
        info_ids = item['info_ids']
        all_titles = item['all_titles']
        publish_time = item['publish_time']
        min_publishtime = item['min_publishtime']
        max_publishtime = item['max_publishtime']
        title_keywords_dic = item['title_keywords_dic']
        content_keywords = item['content_keywords']
        
        # 存入后台的
        if len(item['info_ids']) > cluster_size_threshold:
            logger.info('score: '+str(score))
            logger.info('title: '+str(title))
            logger.info('cluster_id: '+str(cluster_id))
            logger.info('info_ids: '+str(info_ids))
            logger.info('keywords: '+str(keywords))
            logger.info('title_keywords_dic: '+str(title_keywords_dic))
            logger.info('all_titles: '+str(all_titles))
            logger.info('content_keywords: '+str(content_keywords))
            logger.info('publish_time: '+str(publish_time))
            logger.info('min_publishtime: '+str(min_publishtime))
            logger.info('max_publishtime: '+str(max_publishtime))
            logger.info('--------------------------')
            cluster_result_.append(item)
            
        # 不存后台的都保留历史纪录，即使数量是1
        else:
            logger.info('score1: '+str(score))
            logger.info('title1: '+str(title))
            logger.info('cluster_id1: '+str(cluster_id))
            logger.info('info_ids1: '+str(info_ids))
            logger.info('keywords1: '+str(keywords))
            logger.info('title_keywords_dic1: '+str(title_keywords_dic))
            logger.info('all_titles1: '+str(all_titles))
            logger.info('content_keywords1: '+str(content_keywords))
            logger.info('publish_time1: '+str(publish_time))
            logger.info('min_publishtime1: '+str(min_publishtime))
            logger.info('max_publishtime1: '+str(max_publishtime))
            logger.info('++++++++++++++++++++++++++')
            

    # save table cluster log
    save_cluster_log(cluster_result_)
    # save table cluster
    save_cluster(cluster_result_)
    # save cluster info id list
    save_cluster_info(cluster_result_)

if __name__ == '__main__':
    
    print('save_cluster_result...')
