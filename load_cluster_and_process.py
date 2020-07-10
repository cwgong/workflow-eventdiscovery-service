# -*- coding: utf-8 -*-

import io
import json
import time

from event_project_utils import event_merge, cluster_event_complete

def get_standard_time(time_stamp):
    
    timeArray = time.localtime(time_stamp/1000)
    otherStyleTime = time.strftime("%Y年%m月%d日", timeArray)
    return otherStyleTime
    


'''
cluster_dict['keywords']=keywords#title-keywords
cluster_dict['id'] = info_ids[0]
cluster_dict['info_ids'] = info_ids
cluster_dict['info_ids_to_data'] = info_ids_to_data
cluster_dict['title'] = title
cluster_dict['publish_time'] = publish_time
cluster_dict['score'] = _cluster_result_score[key]
cluster_dict['title_keywords_dic'] = _cluster_title_keywords[key]['title_keywords_dic']#有词频信息的title-keywords
cluster_dict['content_keywords'] = _cluster_keywords[key]#title-keywords+content-keywords
cluster_dict['all_titles'] = all_titles_in_cluster
cluster_dict['all_title_words'] = all_titlewords_in_cluster
cluster_dict['all_publishtime'] = all_publishtime_in_cluster
cluster_dict['min_publishtime'] = min(all_publishtime_in_cluster)
cluster_dict['max_publishtime'] = max(all_publishtime_in_cluster)
'''


def triple_info_to_event_info_process(titles_info, cluster_triples_info, filter_cluster_triples_info, cluster_event_infos):    

    for title_info in titles_info:
                
        sentence = title_info['sentence']
        TMP = title_info['TMP']
        RPT = title_info['RPT']
        sentence_info = title_info['sentence_info']
        
        core_words_info = sentence_info['core_words_info']
        core_words = [item['word'] for item in core_words_info]
        
        ner_info = sentence_info['ner_info']
        for a in sentence_info['triple_info']:
            
            triple = a['triple']
            
            if str(triple) not in cluster_triples_info:
                cluster_triples_info[str(triple)] = {'count': 1,
                                                      'TMP': {TMP: 1},
                                                      'RPT': {RPT: 1}}
            else:
                cluster_triples_info[str(triple)]['count'] += 1
            
            # 根据 core_words 过滤 triple
            if triple[1] in core_words:
                
                if str(triple) not in filter_cluster_triples_info:
                    filter_cluster_triples_info[str(triple)] = {'count': 1,
                                                              'TMP': {TMP: 1},
                                                              'RPT': {RPT: 1}}
                else:
                    filter_cluster_triples_info[str(triple)]['count'] += 1
                                                    
                # 用于之后的进一步事件聚类
                event_info = {}
                event_info['triple_info'] = {'triple': triple,
                                             'sentence': sentence}
                event_info['ner_info'] = ner_info
                event_info['TMP'] = TMP
                event_info['RPT'] = RPT
                cluster_event_infos.append(event_info)



def cluster_event_cluster_sort(cluster_event_cluster):
    
    # cluster_event_cluster 按 triple 统计排序 方便观察
    triples_count = {}
    
    for item in cluster_event_cluster:
        t = item['triple_info']['triple']
        sentence = item['triple_info']['sentence']
        TMP = item['TMP']
        RPT = item['RPT']
        ners = [mm['ner_name'] for mm in item['ner_info']]
        if str(t) not in triples_count:
            triples_count[str(t)] = {'count': 1,
                                      'triple':t,
                                      'sentence':{sentence:1},
                                      'TMP': {TMP: 1},
                                      'RPT':{RPT: 1},
                                      'ners': ners
                                      }
        else:
            triples_count[str(t)]['count'] += 1
            
            if sentence not in triples_count[str(t)]['sentence']:
                triples_count[str(t)]['sentence'][sentence] = 1
            else:
                triples_count[str(t)]['sentence'][sentence] += 1
                              
            if TMP not in triples_count[str(t)]['TMP']:
                triples_count[str(t)]['TMP'][TMP] = 1
            else:
                triples_count[str(t)]['TMP'][TMP] += 1
            
            if RPT not in triples_count[str(t)]['RPT']:
                triples_count[str(t)]['RPT'][RPT] = 1
            else:
                triples_count[str(t)]['RPT'][RPT] += 1
                                   
    triples_count = sorted(triples_count.items(), key=lambda x:x[1]['count'], reverse = True)
    
    return triples_count
    

def f_cluster(cluster_event_infos_complete, f1, hot_filter = 1):
    
    # 聚类
    cluster_event_clusters = event_merge(cluster_event_infos_complete)
    
    # 聚类后按簇大小排序
    cluster_event_clusters = sorted(cluster_event_clusters, key=lambda x:len(x), reverse = True)
           
    f1.write('------------' + '\n')
    f1.write('\nevent_clusters:' + '\n\n')
    for cluster_event_cluster in cluster_event_clusters:
        
        # cluster_event_cluster 按 triple 统计排序 方便观察
        triples_count = cluster_event_cluster_sort(cluster_event_cluster)
        
        hot_ = 0
        for _, dic in triples_count:
            count = dic['count']
            hot_ += count
        
        if hot_ <= hot_filter:
            continue
        
        f1.write('--- hot: ' +str(hot_) + ' ---' '\n')
        for _, dic in triples_count:
            
            # 对 dic 中的 sen、TMP、RPT 进行举例选择
            triple = dic['triple']
            s_info = dic['sentence']
            TMP_info = dic['TMP']
            RPT_info = dic['RPT']
            count = dic['count']
            ners = dic['ners']
            
            
            
            s_info = sorted(s_info.items(), key=lambda d:d[1], reverse = True)
            TMP_info = sorted(TMP_info.items(), key=lambda d:d[1], reverse = True)
            RPT_info = sorted(RPT_info.items(), key=lambda d:d[1], reverse = True)
            
            s = ''
            for a, _ in s_info:
                s = a
                break
            
            TMP = ''
            for a, _ in TMP_info:
                if a != '':
                    TMP = a
                    break
                
            RPT = ''
            for a, _ in RPT_info:
                if a != '':
                    RPT = a
                    break
            
            if TMP != '':
                TMP = get_standard_time(TMP)
            
            if RPT != '':
                RPT = get_standard_time(RPT)
            
            f1.write(str(triple) +' count: ' + str(count) +  ' TMP: ' + str(TMP) +  ' RPT: ' + str(RPT) + ' NERs: ' + str(ners) + ' s: ' + str(s) + '\n')
            
            

def write_cluster_info(json_data, f1):
    
    cluster_title = json_data['title']
    cluster_keywords = json_data['keywords']
    hot = len(json_data['info_ids'])
    f1.write('cluster_title:' + cluster_title + '\n')
    f1.write('hot:' + str(hot) + '\n')
    f1.write('cluster_keywords:' + str(cluster_keywords) + '\n')
    f1.write('------------' + '\n')
    f1.write('cluster_info:' + '\n')
    for raw_data in json_data['info_ids_to_data']:
        title = raw_data['title']
        content = raw_data['content']
        event_description = raw_data['event_description']
        
        f1.write('title:' + title + '\n')
        f1.write('event_description:' + event_description + '\n')
        f1.write('content:' + content + '\n')
        f1.write('\n')
        
    f1.write('------------' + '\n')
    min_publishtime = json_data['min_publishtime']
    max_publishtime = json_data['max_publishtime']
    min_publishtime = get_standard_time(min_publishtime)
    max_publishtime = get_standard_time(max_publishtime)
    f1.write('min_publishtime:' + str(min_publishtime) + '\n')
    f1.write('max_publishtime:' + str(max_publishtime) + '\n')

    
    
    
def load_cluster_info_process(cluster_file_path, file_path, hot_filter = 1):

    # 所有簇的事件 event_info 用于进一步聚类
    all_cluster_event_infos = []
    
    with io.open(file_path, "a", encoding='utf-8') as f1:
        with io.open(cluster_file_path, "r", encoding='utf-8') as f:
            while True:
                line = f.readline()
                if len(line) > 0:
                    json_data = json.loads(line)
                    
                    info_ids_to_data = json_data['info_ids_to_data']
                    
                    if len(info_ids_to_data) <= hot_filter:
                        continue
                    
                    write_cluster_info(json_data, f1)
                    
                    # 用于统计与冠词
                    cluster_triples_info = {}
                    filter_cluster_triples_info = {}
                    # 用于簇内进一步聚类, 默认是通过核心动词过滤后的结果
                    cluster_event_infos = []
                    
                    for id_data in info_ids_to_data:
                        
                        titles_info = id_data['titles_info']
                        sentences_info = id_data['sentences_info']
                        triple_info_to_event_info_process(titles_info, cluster_triples_info, filter_cluster_triples_info, cluster_event_infos)
                        triple_info_to_event_info_process(sentences_info, cluster_triples_info, filter_cluster_triples_info, cluster_event_infos)
                    
                    
                    # ---------- cluster_triples_info 排序 -----------
                    cluster_triples_info_ = []
                    cluster_triples_info = sorted(cluster_triples_info.items(), key=lambda d:d[1]['count'], reverse = True)
                    for triple, dic in cluster_triples_info:
                        TMP_dic = dic['TMP']
                        TMP_dic = sorted(TMP_dic.items(), key=lambda d:d[1], reverse = True)
                        RPT_dic = dic['RPT']
                        RPT_dic = sorted(RPT_dic.items(), key=lambda d:d[1], reverse = True)
                        cluster_triples_info_.append([triple, dic['count'], TMP_dic, RPT_dic])
                    
                    filter_cluster_triples_info_ = []
                    filter_cluster_triples_info = sorted(filter_cluster_triples_info.items(), key=lambda d:d[1]['count'], reverse = True)
                    for triple, dic in filter_cluster_triples_info:
                        TMP_dic = dic['TMP']
                        TMP_dic = sorted(TMP_dic.items(), key=lambda d:d[1], reverse = True)
                        RPT_dic = dic['RPT']
                        RPT_dic = sorted(RPT_dic.items(), key=lambda d:d[1], reverse = True)
                        filter_cluster_triples_info_.append([triple, dic['count'], TMP_dic, RPT_dic])
                    
                    print('len(cluster_triples_info_): ', len(cluster_triples_info_))
                    print('len(filter_cluster_triples_info_): ', len(filter_cluster_triples_info_))
                    print('len(cluster_event_infos): ', len(cluster_event_infos))
                    
                    # 补全与簇内事件再聚类
                    # 补全
                    cluster_event_infos_complete = cluster_event_complete(cluster_event_infos)
                    print('len(cluster_event_infos_complete): ', len(cluster_event_infos_complete))
                    
                    all_cluster_event_infos += cluster_event_infos_complete
                    
                    f_cluster(cluster_event_infos_complete, f1)

                    
                
                else:
                    break
                
    return all_cluster_event_infos


def all_cluster_event_infos_process(all_cluster_event_infos, file_path):
    
    with io.open(file_path, "a", encoding='utf-8') as f1:
        f_cluster(all_cluster_event_infos, f1)
    
    
    
    
    
if __name__ == '__main__':
    
    cluster_file_path = 'logs1/cluster_result.txt'
    file_path = 'logs1/cluster_triple_result.txt'
    file_path1 = 'logs1/triple_cluster_result.txt'
    
    all_cluster_event_infos = load_cluster_info_process(cluster_file_path, file_path)
    
    all_cluster_event_infos_process(all_cluster_event_infos, file_path1)
    
    
    
    
    
    
    
    
    