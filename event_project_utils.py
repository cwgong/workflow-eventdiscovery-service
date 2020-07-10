# -*- coding: utf-8 -*-

import re
import io
import json

# 去 “电” 头、去括号、【】 等
# 结果可用于 聚类 和 get parser triple
def semantic_clean(text):
    
    
    # 可能是开头，也可能是结尾，所以需要判断索引位置
    # 理论上一个新闻 text 中只会存在一个 “电头” 
    features = ['日电','日讯','日消息','日报道']
    for fea in features:
        if fea in text:
            fea_ids = text.index(fea)
            if fea_ids < int(1/2 * len(text)):
                text = text[fea_ids+len(fea):]
                break
    
    # 剔除掉 （）、() 中的 “不规范信息”
    special_signs = ["(", "（", "【", "[", '<']
    signs_infos_list = get_special_chunk(text)
    for item in signs_infos_list:
        if item['type'] in special_signs:
            text = text.replace(item['chunk_str'], '')
    return text

# 抽取出 text 中所有的 special sign string 及 offset
def get_special_chunk(text):
    signs_infos_list = []
    
    special_signs = [['(', ')'], ['（', '）'], ['<','>'],['《', '》'], ['【', '】'],['[',']'],['{','}'],
                     ['「', '」'], ['‘', '’'], ['\"', '\"'],['“', '”'], ['\'', '\'']]

    special_signs_rgx_info = []
    for i in range(0,len(special_signs)):
        rgx = re.compile(r'[{0}](.*?)[{1}]'.format(special_signs[i][0],special_signs[i][1]))
        type = special_signs[i][0]
        temp_dic = {}
        temp_dic['rgx'] = rgx
        temp_dic['type'] = type
        special_signs_rgx_info.append(temp_dic)


    for x in special_signs_rgx_info:
        item = x['rgx']
        type = x['type']
        item_rgx = item.finditer(text)
        if item_rgx is not None:
            for m in item_rgx:
                signs_infos = {}
                signs_infos['offset'] = m.span()
                signs_infos['chunk_str'] = m.group(0)
                signs_infos['type'] = type
                signs_infos_list.append(signs_infos)
                
    return signs_infos_list


def title_punctuation_process(title):
    
    title_s_list = title.strip().split(' ')

    return title_s_list


'''
1、动词会存在近义词，如 发布、颁发、印发、考虑利用近义词表进行归并
2、主语或宾语存在如“习近平”、“习近平主席”、“国家主席习近平”、“外商投资法配套法规”、“《外商投资法》配套法规”
   相似可归并，主语和宾语的相似定义为「包含」？，归并时需要衡量其动词的主语、宾语、相关 NER 的相似性
3、利用簇内信息对簇内三元组进行补全，一是为了能够增加其权重，二是能让缺失三元组变的完整。
4、先补全，再归并，再统计
'''

'''
event_info = {}
event_info['triple_info'] = {'triple': triple,
                             'sentence': sentence}
event_info['ner_info'] = ner_info
event_info['TMP'] = TMP
event_info['RPT'] = RPT
'''
def event_merge_condition(event_info, event_info_, synonym_info = {}):
    
    triple_info = event_info['triple_info']
    sub = triple_info['triple'][0]
    v = triple_info['triple'][1]
    obj = triple_info['triple'][2]
    TMP = event_info['TMP']
    #NERs = event_info['NERs']
    
    triple_info_ = event_info_['triple_info']
    sub_ = triple_info_['triple'][0]
    v_ = triple_info_['triple'][1]
    obj_ = triple_info_['triple'][2]
    TMP_ = event_info_['TMP']
    #NERs_ = event_info_['NERs']
    try:
        sub_score = len(set(sub)&set(sub_)) / min([len(set(sub)), len(set(sub_))])
    except:
        sub_score = 0
        
    # 排除掉空字符串的比较 ‘’与‘’
    if sub == sub_:
        sub_score = 1
        
    try:
        obj_score = len(set(obj)&set(obj_)) / min([len(set(obj)), len(set(obj_))])
    except:
        obj_score = 0
    
    if obj == obj_:
        obj_score = 1
    
    # 动作的包含关系
    v_score = len(set(v)&set(v_)) / min([len(set(v)), len(set(v_))])
    
    if v in v_ or v_ in v:
        v_score = 1
    # 动作的同义关系
    if v in synonym_info:
        if v_ in synonym_info[v]:
            v_score = 1
    if v_ in synonym_info:
        if v in synonym_info[v_]:
            v_score = 1
    if sub_score > 0.66 and obj_score > 0.66 and v_score > 0.66 :
        return 1
    
    return 0

# 不仅限于簇内，是对所有 event 的归并
# event = triple (sub, v, obj) + TMP + NERs
def event_merge(event_infos):
    synonym_info = load_synonym('./CoreSynonym.txt')
    event_clusters = []
    for i in range(len(event_infos)):
        print('event_merge process id: ', i)
        event_info = event_infos[i]
        condition = 0 
        for j in range(len(event_clusters)):
            # 只取每个簇的第一个
            event_info_ = event_clusters[j][0] 
            score = event_merge_condition(event_info, event_info_, synonym_info)
            if score == 1:
                condition += 1
                event_clusters[j].append(event_infos[i])
                break

        if condition == 0:
            event_clusters.append([event_infos[i]])
    
    return event_clusters
    
    
def cluster_event_complete(event_infos):
    
    # 为每一个 v 维护一个相应的 sub 和 obj 统计，不含 ‘’ 
    v_info = {}
    
    for event_info in event_infos:
        triple_info = event_info['triple_info']
        sub = triple_info['triple'][0]
        v = triple_info['triple'][1]
        obj = triple_info['triple'][2]
        if v not in v_info:
            sub_count = 1
            if sub == '':
                sub_count = 0
            obj_count = 1
            if obj == '':
                obj_count = 0
            v_info[v] = {'sub':{sub:sub_count},
                         'obj':{obj:obj_count}}
        else:
            if sub != '':
                if sub not in v_info[v]['sub']:
                    v_info[v]['sub'][sub] = 1
                else:
                    v_info[v]['sub'][sub] += 1
            if obj != '':  
                if obj not in v_info[v]['obj']:
                    v_info[v]['obj'][obj] = 1
                else:
                    v_info[v]['obj'][obj] += 1
    
    # 对 v 的 sub 与 obj 排序
    for v, dic in v_info.items():
        v_info[v]['sub'] = sorted(dic['sub'].items(), key=lambda d:d[1], reverse = True)
        v_info[v]['obj'] = sorted(dic['obj'].items(), key=lambda d:d[1], reverse = True)

    # triple sub 与 obj 补全
    event_infos_ = []
    for event_info in event_infos:
        triple_info = event_info['triple_info']
        sub = triple_info['triple'][0]
        v = triple_info['triple'][1]
        obj = triple_info['triple'][2]
        if sub == '':
            sub_ = v_info[v]['sub'][0][0]
            count = v_info[v]['sub'][0][1]
            if count > 1:
                sub = sub_
        
        if obj == '':
            obj_ = v_info[v]['obj'][0][0]
            count = v_info[v]['obj'][0][1]
            if count > 1:
                obj = obj_
        
        triple_info['triple'][0] = sub
        triple_info['triple'][2] = obj
        event_info['triple_info'] = triple_info
        event_infos_.append(event_info)
        
    return event_infos_
    
def all_cluster_triple_merge(triple_infos):
    
    pass
    


def load_synonym(file_path):
    
    synonym_info = {}
    
    with io.open(file_path, "r", encoding='utf-8') as f:
        while True:
            line = f.readline()
            line = line.strip()
            if len(line) > 0:
                if '=' in line:
                    words_in_line = line.split('=')[1].strip().split(' ')
                    #print(words_in_line)
                    for word in words_in_line:
                        if word not in synonym_info:
                            synonym_info[word] = set(words_in_line)
                        else:
                            synonym_info[word] = synonym_info[word] | set(words_in_line)
                
            else:
                break
    
    
    return synonym_info



if __name__ == '__main__':
    
    title = '  中共中央政治局召开会议 分析研究当前经济形势和经济工作 中共中央总书记习近平主持 '
    print(title_punctuation_process(title))
    
    text = '  新华社北京10月31日电（记者闻飞翔）中共中央政治局10月31日召开【今天是星期5】会议，分析研究当前经济形势，部署当前经济工作'
    text = '记者3月22日从省司法厅获悉，近日，青海省政府印发《青海省人民政府关于取消102项证明事项的决定》(以下简称《决定》），决定取消102项涉及企业群众办事创业的证明事项。  据介绍，此次取消的102项证明事项，涉及婚姻家庭、亲属关系、社会保障、财产收入、医疗卫生、户籍身份、劳动就业、教育服务等长期困扰群众的“堵点”“痛点”“难点”问题。《决定》要求对已经公布取消的证明事项一律不得再向企业群众索要，取消后的办理方式，有37项不再要求申请人提交，其余事项改为部门间信息核验、提交有效证照、书面告知承诺等方式。各地区各部门要及时调整政务服务网、政务大厅办事流程和服务方式，方便企业群众办事创业。同时，各级政府及部门要结合取消的证明事项抓紧修改相关文件，以后在制定政府规章、规范性文件时不得新设证明事项。  省司法厅立法二处相关负责人表示，取消无法律法规依据的证明事项，从源头上铲除了奇葩证明、循环证明、重复证明滋生的土壤，真正做到审批更简、监管更强、服务更优，不断提升群众的满意度。(记者 于瑞荣)        '
    print(semantic_clean(text))
    
    s = '"今"天是（星期五）一起去（<吃饭>）,所以“明年”一"起去"{阿萨德快乐}好啊《法法》明天企业所以一起去'
    s = 'sfds(fffffffff)fffffffffffx'
    print(get_special_chunk(s))

    
    
    event_info1 = {'triple_info':{'triple':['国务院办公厅', '发布', '通知']},
                   'TMP':'2019年03月22日',
                   'NERs': []}
    event_info2 = {'triple_info':{'triple':['中国政府网', '公布', '《国务院办公厅关于调整2019年劳动节假期安排的通知》']},
                   'TMP':'2019年03月22日',
                   'NERs': []}
    event_info3 = {'triple_info':{'triple':['国务院办公厅', '发布', '《关于调整2019年劳动节假期安排的通知》']},
                   'TMP':'2019年03月22日',
                   'NERs': []}
    event_info4 = {'triple_info':{'triple':['国务院办公厅', '发布', '通知']},
                   'TMP':'2019年03月22日',
                   'NERs': []}
    event_info5 = {'triple_info':{'triple':['中国政府网', '发布', '通知']},
                   'TMP':'2019年03月22日',
                   'NERs': []}
    event_info6 = {'triple_info':{'triple':['省政府各部门', '发布', '']},
                   'TMP':'2019年03月22日',
                   'NERs': []}
    event_infos = [ event_info1,  event_info2,  event_info3,  event_info4,  event_info5, event_info6]
    
    
    
    event_infos_ = cluster_event_complete(event_infos)
    print(event_infos_)
    
    
    event_clusters = event_merge(event_infos)
    print(event_clusters)
    
    for x in event_clusters:
        print(len(x))
        print(x)
        print('--------------')
    
    
    event_info = {'triple_info': {'triple': ['神雾节能公告', '称', '']}, 'TMP': '2019年03月12日', 'RPT': '2019年03月13日'}
    
    event_info_ = {'triple_info': {'triple': ['早间央行公告', '称', '']}, 'TMP': '2019年03月12日', 'RPT': '2019年03月12日'}
    print(event_merge_condition(event_info, event_info_))
    
    
    
    
    