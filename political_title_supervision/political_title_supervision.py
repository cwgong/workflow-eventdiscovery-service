# -*- coding: utf-8 -*-

import io
import json
import requests

class Political_Title_Supervision(object):
    
    def __init__(self):
        print('Class Political_Title_Supervision initial ...')
        self.abs_neg_strings = []
        self.neg_strings = []
        self.neg_entities = []
        self.neg_entities1 = []
        self.special_sign_1 = []
        self.pos_entities = []
        self.pos_strings = []
        
        self.abs_neg_strings = self.load_abs_neg_strings()
        self.neg_strings = self.load_neg_strings()
        self.neg_entities = self.load_neg_entities()
        self.neg_entities1 = self.load_neg_entities1()
        self.special_sign_1 = self.load_special_sign_1()
        self.pos_entities = self.load_pos_entities()
        self.pos_strings = self.load_pos_strings()
        print('Class Political_Title_Supervision initial finished!')
    
    def f(self, title, title_seg = None):
        
        # 月 日 价格
        # 今日关注
        for abs_neg_string in self.abs_neg_strings:
            if abs_neg_string in title:
                return False
        
        for neg_entity1 in self.neg_entities1:
            if neg_entity1 in title:
                return False
        
        for word in self.special_sign_1:
            if '['+word+']' in title:
                return False
            
        for pos_entiy in self.pos_entities:
            if pos_entiy in title:
                return True   
        
        for neg_entity in self.neg_entities:
            if neg_entity in title:
                return False
            
        for pos_string in self.pos_strings:
            if pos_string in title:
                return True

        if title_seg is not None:
            x = title_seg
        else:
            x = self.split_sentence(title)
        
        x_ = list(filter(lambda x: len(x['word'].strip()) > 0, x))
        
        natures = [a['nature'] for a in x_]
        words = [a['word'] for a in x_]
        
        # p 
        for i in range(0,len(natures)):
            if natures[i] == 'ns':
                if '[' + words[i] + ']' in title:
                    return True
                if '【' + words[i] + '】' in title:
                    return True
                if words[i] + '：' in title:
                    return True
                if words[i] + ':' in title:
                    return True
                
        # n
        for i in range(0,len(natures)):
            if natures[i] == 'st' or natures[i] == 'hy':
                if '[' + words[i] + ']' in title:
                    return False
                if '【' + words[i] + '】' in title:
                    return False
                if words[i] + '：' in title:
                    return False
                if words[i] + ':' in title:
                    return False
        
        # n
        for neg_string in self.neg_strings:
            if neg_string in title:
                return False
            
        # p
        if natures[0] == 'ns':
            return True
        
        return True
    
    def load_abs_neg_strings(self):
        
        abs_neg_strings = []
        with io.open('./political_title_supervision/title_supervision_config/abs_neg_strings.txt', "r", encoding='utf-8') as f:
            while True:
                line = f.readline()
                if len(line.strip()) > 0:
                    abs_neg_strings.append(line.strip())   
                else:
                    break
        print('abs_neg_strings: ', len(abs_neg_strings))
    
        return abs_neg_strings
    
    def split_sentence(self, sen):
        nlp_url = 'http://hanlp-rough-service:31001/hanlp/segment/rough'
        try:
            cut_sen = dict()
            cut_sen['content'] = sen
            data = json.dumps(cut_sen).encode("UTF-8")
            cut_response = requests.post(nlp_url, data=data, headers={'Connection':'close'})
            cut_response_json = cut_response.json()
            return cut_response_json['data']
        except Exception as e:
            print.exception("Exception: {}".format(e))
            return []
        
    def load_neg_strings(self):
        
        neg_strings = []
        with io.open('./political_title_supervision/title_supervision_config/neg_string.txt', "r", encoding='utf-8') as f:
            while True:
                line = f.readline()
                if len(line.strip()) > 0:
                    neg_strings.append(line.strip())   
                else:
                    break
        print('neg_strings: ', len(neg_strings))
        
        return neg_strings
    
    def load_neg_entities(self):
        
        neg_entities = []
        with io.open('./political_title_supervision/title_supervision_config/neg_entity.txt', "r", encoding='utf-8') as f:
            while True:
                line = f.readline()
                if len(line.strip()) > 0:
                    neg_entities.append(line.strip())   
                else:
                    break
        print('neg_entities: ', len(neg_entities))
        
        return neg_entities
    
    def load_neg_entities1(self):
        
        neg_entities1 = []
        with io.open('./political_title_supervision/title_supervision_config/neg_entity1.txt', "r", encoding='utf-8') as f:
            while True:
                line = f.readline()
                if len(line.strip()) > 0:
                    neg_entities1.append(line.strip().split(' ')[0])   
                else:
                    break
        print('neg_entities1: ', len(neg_entities1))
        
        return neg_entities1
    def load_special_sign_1(self):
        
        special_sign_1 = []
        with io.open('./political_title_supervision/title_supervision_config/special_sign1', "r", encoding='utf-8') as f:
            while True:
                line = f.readline()
                if len(line.strip()) > 0:
                    special_sign_1.append(line.strip().split(' ')[0])   
                else:
                    break
        print('special_sign_1: ', len(special_sign_1))
        
        return special_sign_1
    
    def load_pos_entities(self):
        
        pos_entities = []
        with io.open('./political_title_supervision/title_supervision_config/pos_entity.txt', "r", encoding='utf-8') as f:
            while True:
                line = f.readline()
                if len(line.strip()) > 0:
                    pos_entities.append(line.strip().split(' ')[0])   
                else:
                    break
        print('pos_entities: ', len(pos_entities))
        
        return pos_entities
    
    def load_pos_strings(self):
        
        pos_strings = []
        with io.open('./political_title_supervision/title_supervision_config/pos_string.txt', "r", encoding='utf-8') as f:
            while True:
                line = f.readline()
                if len(line.strip()) > 0:
                    pos_strings.append(line.strip())   
                else:
                    break
        print('pos_strings: ', len(pos_strings))
        
        return pos_strings
            


    
if __name__ == '__main__':
    
     title = '台州椒江：人才项目“绩效管理”激发创业创新活力'
     
     
     p = Political_Title_Supervision()
     print(p.f(title))
     
     
     

