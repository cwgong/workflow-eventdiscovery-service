# -*- coding: utf-8 -*-
'''
原生 LTP 分词、词性、ner、parser、及 SRL
特点：各部分功能可拆解，灵活
     可拆解部分利用 ori_ 函数
'''

from pyltp import Segmentor, Postagger, NamedEntityRecognizer, Parser, SementicRoleLabeller
import os

class HIT_LTP():

    def __init__(self, MODELDIR):
        
        self.MODELDIR = MODELDIR
        
        self.segmentor = Segmentor()
        self.segmentor.load(os.path.join(MODELDIR, "cws.model"))
        
        # postags = 863 词性标注集
        # https://ltp.readthedocs.io/zh_CN/latest/appendix.html#id3
        self.postagger = Postagger()
        self.postagger.load(os.path.join(MODELDIR, "pos.model"))
        
        self.recognizer = NamedEntityRecognizer()
        self.recognizer.load(os.path.join(MODELDIR, "ner.model"))
        
        self.parser = Parser()
        self.parser.load(os.path.join(MODELDIR, "parser.model"))
        
        self.srler = SementicRoleLabeller()
        self.srler.load(os.path.join(MODELDIR, "pisrl.model"))
        
    def ori_segment(self, sentence):
        
        words = self.segmentor.segment(sentence)
        words = list(words)
        return words
    
    def ori_pos(self, words):
        
        postags = self.postagger.postag(words)
        postags = list(postags)
        return postags
    
    def ori_ner(self, words, postags):
        
        netags = self.recognizer.recognize(words, postags)
        netags = list(netags)
        return netags
    
    def ori_parser(self, words, postags):
        
        arcs = self.parser.parse(words, postags)
        arcs = [[arc.head, arc.relation] for arc in arcs]
        return arcs
        
    # 在哈工大 ltp 中，默认为最细粒度分词
    def std_seg(self, sentence):
        
        words = self.segmentor.segment(sentence)
        postags = self.postagger.postag(words)
        
        terms = []
        offe = 0
        for word, postag in zip(words, postags):
            term = {}
            term['word'] = word 
            term['nature'] = postag
            term['offset'] = offe
            offe += len(word)
            terms.append(term)
            
        return terms
    
    # 加入 ner 的分词，相当于粗粒度分词
    def nlp_seg(self, sentence):
        
        words = self.segmentor.segment(sentence)
        postags = self.postagger.postag(words)
        netags = self.recognizer.recognize(words, postags)
        words = list(words)
        postags = list(postags)
        netags = list(netags) # B-Ni E-Ni O O S-Ni O S-Nh O B-Ni E-Ni O S-Nh O O S-Nh O O O O S-Ns O S-Ns O
        
        chunks = self.get_ner_info(netags) # [('Ni', 0, 2), ('Ni', 4, 5), ('Nh', 6, 7), ('Ni', 8, 10), ('Nh', 11, 12), ('Nh', 14, 15), ('Ns', 19, 20), ('Ns', 21, 22)]
        
        num_ners = len(chunks)
        # 得到加入 ner 的 words_ 与 postags_
        words_ = []
        postags_ = []
        if num_ners != 0:
            ner_index = 0
            length = 0
            for i in range(len(words)):
                j = i + length
                if j < len(words):
                    ner_type = chunks[ner_index][0]
                    ner_start = chunks[ner_index][1]
                    ner_end = chunks[ner_index][2]
                    word = words[j]
                    postag = postags[j]
                    if j == ner_start:
                        for k in range(ner_start+1, ner_end):
                            word += words[k]
                            length += 1
                        postag = ner_type.lower()
                        if ner_index < len(chunks)-1:
                            ner_index += 1
                    words_.append(word)
                    postags_.append(postag)
        
        terms = []
        offe  = 0
        for word, postag in zip(words_, postags_):
            term = {}
            term['word'] = word 
            term['nature'] = postag
            term['offset'] = offe
            offe += len(word)
            terms.append(term)
            
        return terms

    def std_analysis(self, sentence):
        
        data = {}
        words = self.segmentor.segment(sentence)
        postags = self.postagger.postag(words)
        words = list(words)
        postags = list(postags)
        
        arcs = self.parser.parse(words, postags)
        arcs_ = [[arc.head, arc.relation] for arc in arcs]
        child_dict_list = self.build_parse_child_dict(words, postags, arcs)
        
        data['words'] = words
        data['postags'] = postags
        data['arcs'] = arcs_
        data['child_dict_list'] = child_dict_list
        
        return data
    
    def nlp_analysis(self, sentence):
        
        data = {}
        words = self.segmentor.segment(sentence)
        postags = self.postagger.postag(words)
        netags = self.recognizer.recognize(words, postags)
        words = list(words)
        postags = list(postags)
        netags = list(netags) # B-Ni E-Ni O O S-Ni O S-Nh O B-Ni E-Ni O S-Nh O O S-Nh O O O O S-Ns O S-Ns O
        
        chunks = self.get_ner_info(netags) # [('Ni', 0, 2), ('Ni', 4, 5), ('Nh', 6, 7), ('Ni', 8, 10), ('Nh', 11, 12), ('Nh', 14, 15), ('Ns', 19, 20), ('Ns', 21, 22)]
        
        num_ners = len(chunks)
        # 得到加入 ner 的 words_ 与 postags_
        words_ = []
        postags_ = []
        if num_ners != 0:
            ner_index = 0
            length = 0
            for i in range(len(words)):
                j = i + length
                if j < len(words):
                    ner_type = chunks[ner_index][0]
                    ner_start = chunks[ner_index][1]
                    ner_end = chunks[ner_index][2]
                    word = words[j]
                    postag = postags[j]
                    if j == ner_start:
                        for k in range(ner_start+1, ner_end):
                            word += words[k]
                            length += 1
                        postag = ner_type.lower()
                        if ner_index < len(chunks)-1:
                            ner_index += 1
                    words_.append(word)
                    postags_.append(postag)
        
        arcs = self.parser.parse(words_, postags_)
        arcs_ = [[arc.head, arc.relation] for arc in arcs]
        child_dict_list = self.build_parse_child_dict(words_, postags_, arcs)
        
        data['words'] = words_
        data['postags'] = postags_
        data['arcs'] = arcs_
        data['child_dict_list'] = child_dict_list
        return data
            
    
    # 基于“细粒度词”的 ner
    def ner(self, sentence):
        
        words = self.segmentor.segment(sentence)
        postags = self.postagger.postag(words)
        netags = self.recognizer.recognize(words, postags)
        words = list(words)
        postags = list(postags)
        netags = list(netags) # B-Ni E-Ni O O S-Ni O S-Nh O B-Ni E-Ni O S-Nh O O S-Nh O O O O S-Ns O S-Ns O
        chunks = self.get_ner_info(netags) # [('Ni', 0, 2), ('Ni', 4, 5), ('Nh', 6, 7), ('Ni', 8, 10), ('Nh', 11, 12), ('Nh', 14, 15), ('Ns', 19, 20), ('Ns', 21, 22)]
        
        ner_info = []
        for chunk in chunks:
            ner_type = chunk[0]
            ner_start = chunk[1]
            ner_end = chunk[2]
            ner_name = ''.join(words[ner_start:ner_end])
            ner_offe = 0
            for i in range(len(words)):
                if i == ner_start:
                    break
                ner_offe += len(words[i])
            ner_info.append({'ner_name': ner_name,
                              'ner_type': ner_type,
                              'ner_offe': ner_offe
                              })
        return ner_info

    def parser(self, sentence):
        
        words = self.segmentor.segment(sentence)
        postags = self.postagger.postag(words)
        arcs = self.parser.parse(words, postags)
        arcs = [[arc.head, arc.relation] for arc in arcs]
        
        return arcs
    
    # 可能会有多个
    def get_core_words(self, sentence, words = None, postags = None):
        
        core_words_info = []
        core_words_indexs = []
        if words is None:
            words = self.segmentor.segment(sentence)
            words = list(words)
        if postags is None:
            postags = self.postagger.postag(words)
            postags = list(postags)
        arcs = self.parser.parse(words, postags)
        arcs_ = [[arc.head, arc.relation] for arc in arcs]
        child_dict_list = self.build_parse_child_dict(words, postags, arcs)
        for i in range(len(arcs_)):
            if arcs_[i][1] == 'HED':
                core_words_indexs.append(i)
                self.complete_core_words(core_words_indexs, i, child_dict_list)
                    
        
        for i in core_words_indexs:
            word = words[i]
            offe = len(''.join(words[0:i]))
            temp_dic = {}
            temp_dic['word'] = word
            temp_dic['offe'] = offe
            core_words_info.append(temp_dic)
                    
        return core_words_info
    
    # 为了更灵活，words = None, postags = None 可解耦
    def get_srl_triple(self, sentence, words = None, postags = None):
        
        data = {}
        if words is None:
            words = self.segmentor.segment(sentence)
            words = list(words)
        if postags is None:
            postags = self.postagger.postag(words)
            postags = list(postags)
        netags = self.recognizer.recognize(words, postags)
        netags = list(netags)
        arcs = self.parser.parse(words, postags)
        arcs_ = [[arc.head, arc.relation] for arc in arcs]
        roles = self.srler.label(words, postags, arcs) 
        
        # 可能有多组角色
        triple_info = []
        for role in roles:
            
            tem_dic = {}
            triple = ['', '', '']
            TMP = ''
            LOC = ''
            
            role = role.index, "".join(
                ["%s:(%d,%d)" % (arg.name, arg.range.start, arg.range.end) for arg in role.arguments])
            
            predicate = words[role[0]]
            
            triple[1] = predicate
                  
            args = role[1].split(")")
            args.remove('')
            for ele in args:
                ele = ele.split(":")
                if ele[0] == "A0":
                    index = ele[1][1:].split(",")
                    A0 = words[int(index[0]):int(index[1]) + 1]
                    A0_str = "".join(A0)
                    triple[0] = A0_str
                if ele[0] == "A1":
                    index = ele[1][1:].split(",")
                    A1 = words[int(index[0]):int(index[1]) + 1]
                    A1_str = "".join(A1)
                    triple[2] = A1_str
                if ele[0] == "TMP":
                    index = ele[1][1:].split(",")
                    tmp = words[int(index[0]):int(index[1]) + 1]
                    tmp_str = "".join(tmp)
                    TMP = tmp_str
                if ele[0] == "LOC":
                    index = ele[1][1:].split(",")
                    loc = words[int(index[0]):int(index[1]) + 1]
                    loc_str = "".join(loc)
                    LOC = loc_str

            tem_dic['role'] = role
            tem_dic['predicate'] = predicate
            tem_dic['triple'] = triple
            tem_dic['TMP'] = TMP
            tem_dic['LOC'] = LOC
            
            triple_info.append(tem_dic)
        
        chunks = self.get_ner_info(netags) # [('Ni', 0, 2), ('Ni', 4, 5), ('Nh', 6, 7), ('Ni', 8, 10), ('Nh', 11, 12), ('Nh', 14, 15), ('Ns', 19, 20), ('Ns', 21, 22)]
        ner_info = []
        for chunk in chunks:
            ner_type = chunk[0]
            ner_start = chunk[1]
            ner_end = chunk[2]
            ner_name = ''.join(words[ner_start:ner_end])
            ner_offe = 0
            for i in range(len(words)):
                if i == ner_start:
                    break
                ner_offe += len(words[i])
            ner_info.append({'ner_name': ner_name,
                             'ner_type': ner_type,
                             'ner_offe': ner_offe
                             })
        data['words'] = words
        data['postags'] = postags
        data['arcs'] = arcs_
        data['triple_info'] = triple_info
        data['ner_info'] = ner_info
            
        return data
    
    def get_parser_triple(self, sentence, words = None, postags = None):
        
        data = {}
        if words is None:
            words = self.segmentor.segment(sentence)
            words = list(words)
        if postags is None:
            postags = self.postagger.postag(words)
            postags = list(postags)
        
        netags = self.recognizer.recognize(words, postags)
        netags = list(netags)
        arcs = self.parser.parse(words, postags)
        arcs_ = [[arc.head, arc.relation] for arc in arcs]
        child_dict_list = self.build_parse_child_dict(words, postags, arcs)

        triple_info = []
        for index in range(len(postags)):
            # 抽取以谓词为中心的事实三元组
            if postags[index] == 'v':
                child_dict = child_dict_list[index]
                
                # 主谓宾
                if 'SBV' in child_dict and 'VOB' in child_dict:
                    e1 = self.complete_e(words, postags, child_dict_list, child_dict['SBV'][0])
                    r = words[index]
                    e2 = self.complete_e(words, postags, child_dict_list, child_dict['VOB'][0])
                    temp_dic = {}
                    temp_dic['triple'] = [e1, r, e2]
                    temp_dic['type'] = '主谓宾'
                    triple_info.append(temp_dic)
                    
                # 定语后置，动宾关系
                # 进行v 正式 访问vob 的 缅甸国务资政昂山素季sbv
                # 动宾，补主语
                elif arcs[index].relation == 'ATT':
                    if 'VOB' in child_dict:
                        e1 = self.complete_e(words, postags, child_dict_list, arcs[index].head - 1)
                        r = words[index]
                        e2 = self.complete_e(words, postags, child_dict_list, child_dict['VOB'][0])
                        temp_string = r+e2
                        if temp_string == e1[:len(temp_string)]:
                            e1 = e1[len(temp_string):]
                        if temp_string not in e1:
                            temp_dic = {}
                            temp_dic['triple'] = [e1, r, e2]
                            temp_dic['type'] = '补主'
                            triple_info.append(temp_dic)
    
                # 含有介宾关系的主谓动补关系
                # 哈立德sbv 居住 在cmp(动补结构) 土耳其pob
                # 主谓，补宾语
                elif 'SBV' in child_dict and 'CMP' in child_dict:
                    #e1 = words[child_dict['SBV'][0]]
                    e1 = self.complete_e(words, postags, child_dict_list, child_dict['SBV'][0])
                    cmp_index = child_dict['CMP'][0]
                    r = words[index] + words[cmp_index]
                    if 'POB' in child_dict_list[cmp_index]:
                        e2 = self.complete_e(words, postags, child_dict_list, child_dict_list[cmp_index]['POB'][0])
                        temp_dic = {}
                        temp_dic['triple'] = [e1, r, e2]
                        temp_dic['type'] = '补宾'
                        triple_info.append(temp_dic)
                
                # 主谓
                elif 'SBV' in child_dict:
                    e1 = self.complete_e(words, postags, child_dict_list, child_dict['SBV'][0])
                    r = words[index]
                    temp_dic = {}
                    temp_dic['triple'] = [e1, r, '']
                    temp_dic['type'] = '主谓'
                    triple_info.append(temp_dic)
                
                # 谓宾
                elif 'VOB' in child_dict:
                    r = words[index]
                    e2 = self.complete_e(words, postags, child_dict_list, child_dict['VOB'][0])
                    temp_dic = {}
                    temp_dic['triple'] = ['', r, e2]
                    temp_dic['type'] = '谓宾'
                    triple_info.append(temp_dic)
                
                # FOB 宾语前置  '中泰数字经济合作部级对话机制第一次会议在云南昆明召开'
                elif 'FOB' in child_dict:
                    r = words[index]
                    e2 = self.complete_e(words, postags, child_dict_list, child_dict['FOB'][0])
                    temp_dic = {}
                    temp_dic['triple'] = ['', r, e2]
                    temp_dic['type'] = '宾前'
                    triple_info.append(temp_dic)
        chunks = self.get_ner_info(netags) # [('Ni', 0, 2), ('Ni', 4, 5), ('Nh', 6, 7), ('Ni', 8, 10), ('Nh', 11, 12), ('Nh', 14, 15), ('Ns', 19, 20), ('Ns', 21, 22)]
        ner_info = []
        for chunk in chunks:
            ner_type = chunk[0]
            ner_start = chunk[1]
            ner_end = chunk[2]
            ner_name = ''.join(words[ner_start:ner_end])
            ner_offe = 0
            for i in range(len(words)):
                if i == ner_start:
                    break
                ner_offe += len(words[i])
            ner_info.append({'ner_name': ner_name,
                             'ner_type': ner_type,
                             'ner_offe': ner_offe
                             })
    
        core_words_info = self.get_core_words(sentence, words = words, postags = postags)
        
        triple_info, core_words_info_ = self.triple_info_futher_merge(core_words_info, triple_info)

        data['words'] = words
        data['postags'] = postags
        data['arcs'] = arcs_
        data['core_words_info'] = core_words_info_
        data['triple_info'] = triple_info
        data['ner_info'] = ner_info
        return data
    
    # 当三元组的谓词在 core_words_info 中时（谓词并列关系 COO）：
    # 如果谓词连续，且一个 triple 缺主语，一个缺宾语，则合并两谓词与主与宾语
    # 如果谓词不连续，且 triple 存在主语缺失或是宾语缺失的情况，则分别补全主语和宾语
    def triple_info_futher_merge(self, core_words_info, triple_info):
        
        core_words_info_ = []
        for i in range(len(core_words_info)-1):
            # 合并后需返回合并后的 core_words_info
            if core_words_info[i]['offe'] + len(core_words_info[i + 1]['word']) == core_words_info[i + 1]['offe']:  # 相邻
                triple_ = ['', '', '']
                condition = 0
                #print('len(triple_info)',len(triple_info))
                for j in range(len(triple_info)):
                    #print('j', j)
                    #print('triple_info', triple_info)
                    if triple_info[j]['triple'][1] == core_words_info[i]['word']:
                        if j+1 < len(triple_info):
                            if triple_info[j+1]['triple'][1] == core_words_info[i+1]['word']:
                                triple_[0] = triple_info[j]['triple'][0]
                                triple_[2] = triple_info[j + 1]['triple'][2]
                                triple_[1] = triple_info[j]['triple'][1] + triple_info[j + 1]['triple'][1]
                                triple_dic = {}
                                triple_dic['triple'] = triple_
                                triple_dic['type'] = '主谓宾'
                                triple_info[j] = triple_dic
                                condition = 1
                                break
                if condition == 1:
                    core_words_info_.append({'word': triple_[1],
                                             'offe': core_words_info[i]['offe']})
                else:
                    core_words_info_.append(core_words_info[i])
            else:  # 不相邻
                sub = ''
                obj = ''
                for triple in triple_info:
                    if triple['triple'][0] != '':
                        sub = triple['triple'][0]
                    if triple['triple'][2] != '':
                        obj = triple['triple'][2]
                for triple in triple_info:
                    if triple['triple'][0] == '':
                        triple['triple'][0] = sub
                    if triple['triple'][2] == '':
                        triple['triple'][2] = obj
                core_words_info_.append(core_words_info[i])
        
        # 补最后一个
        for i in range(len(core_words_info)):
            if i == len(core_words_info)-1:
                core_words_info_.append(core_words_info[i])
                
        # print(core_words_info)
        # print(triple_info)
        return triple_info, core_words_info_
    
    def restart(self):
        
        self.segmentor.release()
        self.postagger.release()
        self.recognizer.release()
        self.parser.release()
        self.srler.release()
    
        self.segmentor = Segmentor()
        self.segmentor.load(os.path.join(self.MODELDIR, "cws.model"))
        self.postagger = Postagger()
        self.postagger.load(os.path.join(self.MODELDIR, "pos.model"))
        self.recognizer = NamedEntityRecognizer()
        self.recognizer.load(os.path.join(self.MODELDIR, "ner.model"))
        self.parser = Parser()
        self.parser.load(os.path.join(self.MODELDIR, "parser.model"))
        self.srler = SementicRoleLabeller()
        self.srler.load(os.path.join(self.MODELDIR, "pisrl.model"))
    
    def release(self):
        
        self.segmentor.release()
        self.postagger.release()
        self.recognizer.release()
        self.parser.release()
        self.srler.release()
    
    # =================== 以下为相关工具方法 ===================  ===================  ===================  =================== 
    def get_ner_type(self, tag_name):

        tag_class = tag_name.split('-')[0] # B I S E O
        tag_type = tag_name.split('-')[-1] # Ni Ns Nh
        return tag_class, tag_type
    
    def get_ner_info(self, netags):
        
        default = "O"
        
        chunks = []
        
        # 定义 类别 和 起始索引
        chunk_type, chunk_start = None, None
        
        for i, tok in enumerate(netags):
            # End of a chunk 1
            if tok == default and chunk_type is not None:
                # Add a chunk.
                chunk = (chunk_type, chunk_start, i)
                chunks.append(chunk)
                
                chunk_type, chunk_start = None, None
    
            elif tok != default:
                tok_chunk_class, tok_chunk_type = self.get_ner_type(tok)
                # 处理 tok_chunk_class
                if tok_chunk_class != 'e' and tok_chunk_class != 'm':
                    # 第一次...
                    # start of a chunk
                    if chunk_type is None:
                        chunk_type, chunk_start = tok_chunk_type, i
                    
                    # End of a chunk + start of a chunk!
                    elif tok_chunk_type != chunk_type or tok_chunk_class == "b" or tok_chunk_class == "s":
                        chunk = (chunk_type, chunk_start, i)
                        chunks.append(chunk)
                        chunk_type, chunk_start = tok_chunk_type, i
            else:
                pass
    
        # end condition
        if chunk_type is not None:
            chunk = (chunk_type, chunk_start, len(netags))
            chunks.append(chunk)
    
        return chunks
    
    def build_parse_child_dict(self, words, postags, arcs):
        """
        为句子中的每个词语维护一个保存句法依存儿子节点的字典
        Args:
            words: 分词列表
            postags: 词性列表
            arcs: 句法依存列表
        """
        child_dict_list = []
        for index in range(len(words)):
            child_dict = dict()
            for arc_index in range(len(arcs)):
                if arcs[arc_index].head == index + 1:
                    if arcs[arc_index].relation in child_dict:
                        child_dict[arcs[arc_index].relation].append(arc_index)
                    else:
                        child_dict[arcs[arc_index].relation] = []
                        child_dict[arcs[arc_index].relation].append(arc_index)

            child_dict_list.append(child_dict)
        return child_dict_list
    
    '''
    # 1、ATT定中关系，2、动宾短语实体，3、从父节点向子节点遍历
    def complete_e(self, words, postags, child_dict_list, word_index):
        """
        完善识别的部分实体
        """
        child_dict = child_dict_list[word_index]
        prefix = ''
        if 'ATT' in child_dict:
            for i in range(len(child_dict['ATT'])):
                prefix += self.complete_e(words, postags, child_dict_list, child_dict['ATT'][i])
        
        postfix = ''
        if postags[word_index] == 'v':
            if 'VOB' in child_dict:
                postfix += self.complete_e(words, postags, child_dict_list, child_dict['VOB'][0])
            if 'SBV' in child_dict:
                prefix = self.complete_e(words, postags, child_dict_list, child_dict['SBV'][0]) + prefix
    
        return prefix + words[word_index] + postfix
    '''
    '''
    def complete_e(self, words, postags, child_dict_list, word_index):
        """
        完善识别的部分实体
        """
        child_dict = child_dict_list[word_index]
        prefix = ''
        postfix = ''
        if 'ATT' in child_dict:
            for i in range(len(child_dict['ATT'])):
                prefix += self.complete_e(words, postags, child_dict_list, child_dict['ATT'][i])
        if 'COO' in child_dict:
            for i in range(len(child_dict['COO'])):
                postfix += self.complete_e(words, postags, child_dict_list, child_dict['COO'][i])
    
        if postags[word_index] == 'v':
            if 'VOB' in child_dict:
                postfix += self.complete_e(words, postags, child_dict_list, child_dict['VOB'][0])
            if 'SBV' in child_dict:
                prefix = self.complete_e(words, postags, child_dict_list, child_dict['SBV'][0]) + prefix
    
        return prefix + words[word_index] + postfix
    '''
    def complete_e(self, words, postags, child_dict_list, word_index):
        """
        完善识别的部分实体
        """
        child_dict = child_dict_list[word_index]
        prefix = ''
        postfix = ''
        if 'ATT' in child_dict:
            for i in range(len(child_dict['ATT'])):
                prefix += self.complete_e(words, postags, child_dict_list, child_dict['ATT'][i])
        if 'COO' in child_dict:
            for i in range(len(child_dict['COO'])):
                if child_dict['COO'][i]-word_index==1:#如果并列的主语和宾语在原文中有分割，则用‘、’分割
                # if postags[child_dict['COO'][i]]=='j':#考虑词性，可能不够全面
                    postfix += self.complete_e(words, postags, child_dict_list, child_dict['COO'][i])
                else:
                    postfix += '、' + self.complete_e(words, postags, child_dict_list, child_dict['COO'][i])
    
        if postags[word_index] == 'v':
            if 'VOB' in child_dict:
                postfix += self.complete_e(words, postags, child_dict_list, child_dict['VOB'][0])
            if 'SBV' in child_dict:
                prefix = self.complete_e(words, postags, child_dict_list, child_dict['SBV'][0]) + prefix
    
        return prefix + words[word_index] + postfix

    # 完善 HED 的 COO 关系
    def complete_core_words(self, core_words_indexs, hed_index, child_dict_list):
        
        if 'COO' in child_dict_list[hed_index].keys():
            core_words_indexs += child_dict_list[hed_index]['COO']
            for i in child_dict_list[hed_index]['COO']:
                self.complete_core_words(core_words_indexs, i, child_dict_list)



# Q1: 是否可以将 core word 的 COO 主语和宾语进行替换？

if __name__ == '__main__':
    
     # =============== =============================== #
     MODELDIR = 'ltp_data_v3.4.0'
     hit_ltp =  HIT_LTP(MODELDIR)
     #load_user_dict(hanlp_ltp, './dict/user_dict.txt')
     # =============== =============================== #
     
     
     
     s1 = '中共中央政治局常委、国务院总理李克强在山东省委书记姜异康、省长郭树清陪同下，在济南、德州考察'
     s = '习近平主持会议，中共中央政治局委员、中央书记处书记、全国人大常委会党员副委员长、国务院副总理、国务委员、最高人民法院院长、最高人民检察院检察长、全国政协党员副主席等出席会议'
     s = '胡锦涛出席会议并讲话并主持会议'
     s = '10月24日至26日国家工商总局副局长王江平赴湖南省考察调研公用企业专项'
     s = '习近平主持召开中共中央政治局会议 分析研究当前经济形势和经济工作'
     s = '新华社北京10月31日电中共中央政治局10月31日召开会议，分析研究当前经济形势，部署当前经济工作'
     s = '聂辰席主持召开总局党组会议传达学习习近平总书记全国两会期间重要讲话和全国两会精神'
     s = '[公司信息]【增减持】德基科技控股获主席蔡鸿能增持29.2万股'
     s = '中央政治局召开会议 习近平主持 李克强韩正栗战书等出席'
     s = '中共中央政治局10月31日召开会议，分析研究当前经济形势，部署当前经济工作'
     s = '习近平赴陕西西安考察调研 李克强、汪洋、栗战书等陪同'
     s = '中共中央政治局召开会议 分析研究当前经济形势和经济工作 中共中央总书记习近平主持'
     s = '并主持召开座谈会'
     s = '3月15日下午，聂辰席同志主持召开总局党组会议，传达学习习近平总书记全国两会期间重要讲话精神和全国两会精神，并就抓好贯彻落实作出部署'
     s = '房地产税立法已转全国人大'
     s = '记者21日从国家税务总局了解到，国家税务总局近日制发《2019年深化增值税改革纳税服务工作方案》推出20项硬举措，以便利高效的纳税服务促进纳税人更好享受深化增值税改革政策红利，切实增强纳税人获得感'
     s1 = '在商务部21日举行的例行新闻发布会上，发言人高峰表示，下一步将研究促进和规范网络零售市场的举措，推动网络零售市场健康、稳定、创新发展'
     s = '中国人民银行行长易纲日前在博鳌亚洲论坛2018年年会上宣布多项金融开放举措，其中3条涉及资本市场领域：将证券公司、基金管理公司、期货公司等机构的外资持股比例的上限放宽到51%，3年以后不再设限'
     s = '《 人民日报 》'
     s = '中国互金协会组织召开防范化解高息现金贷等业务风险专题座谈会'
     s = '中美经贸高级别磋商将于近期分别在北京和华盛顿举行'
     s = '国家统计局局长宁吉喆：明年实现GDP全国统一核算'
     s = '拼多多涨5.17%'
     words = ["青海", "省政府", "印发", "《青海省人民政府关于取消102项证明事项的决定》"]
     postags = ['ns', 'n', 'v', 'n']
     s = '特朗普疑似回应波音事故：现在的飞机太复杂，连飞行员都不需要'
     s = '在华盛顿举行第九轮中美经贸高级别磋商'
     s = ' 财政部、税务总局、海关总署联合发布《关于深化增值税改革有关政策的公告》'
     s = '中共中央政治局常委、国务院总理李克强到财政部、税务总局考察'
     s = '浙江省企业家投资合作考察团到贵州考察'
     words = ['浙江省企业家投资合作考察团', '到', '贵州', '考察']
     s = '国务院总理李克强3月20日主持召开国务院常务会议'
     s = '在商务部21日举行的例行新闻发布会上'
     s = '国家主席习近平分别致电莫桑比克总统纽西、津巴布韦总统姆南加古瓦和马拉维总统穆塔里卡'
     words =['国务院', '总理', '李克强', '3月', '20日', '组织召开', '国务院', '常务', '会议']
     postags = ['ni', 'n', 'nh', 'nt', 'nt', 'v', 'ni', 'b', 'n']
     s = '中泰数字经济合作部级对话机制第一次会议在云南昆明召开'
     s = '由中国工业和信息化部、泰国数字经济和社会部共同主办的中泰数字经济合作部级对话机制第一次会议在昆明举行' # FOB 需要补充
     s = '国家电网公司3月8日在京召开泛在电力物联网建设工作部署电视电话会议'
     
     # COO 关系的动词 补全主语和宾语会有一些问题
     s = '市督办督查局党组书记、局长马骁带队赴修文县、开阳县督导“两会”期间信访维稳工作'
     words = ["市", "督办", "督查局", "党组", "书记", "、", "局长", "马骁", "带队", "赴", "修文县", "、", "开阳县", "督导", "“两会”", "期间", "信访", "维稳", "工作"]
     postags =["n", "v", "n", "n", "n", "wp", "n", "nh", "v", "v", "ns", "wp", "ns", "v", "n", "nd", "n", "v", "v"]
     
     
     
     # 词性的序列标注也很重要
     s = s1
     print('s: ', s) 
     print('len(s): ', len(s)) 
     
     print('\n--------------  words_, postags_, arcs, child_dict_list --------------')
     data = hit_ltp.std_analysis(s)
     for w, p, a, c in zip(data['words'], data['postags'], data['arcs'], data['child_dict_list']):
         print('{}\t{}\t{}\t{}'.format(w, p, a, c))
     
     print('\n--------------  std_seg --------------')
     print(hit_ltp.std_seg(s))
     
     print('\n--------------  nlp_seg --------------')
     print(hit_ltp.nlp_seg(s))
     
     print('\n--------------  ner --------------')
     ner_infos = hit_ltp.ner(s)
     print(ner_infos)
     
     print('\n--------------  std_analysis --------------')
     data = hit_ltp.std_analysis(s)
     print('words: ', data['words'])
     print('postags: ', data['postags'])
     print('arcs: ', data['arcs'])
     print('child_dict_list: ', data['child_dict_list'])
     
     print('\n--------------  nlp_analysis --------------')
     data = hit_ltp.nlp_analysis(s)
     print('words: ', data['words'])
     print('postags: ', data['postags'])
     print('arcs: ', data['arcs'])
     print('child_dict_list: ', data['child_dict_list'])
     
     print('\n--------------  core words --------------')
     core_words_info = hit_ltp.get_core_words(s)
     print(core_words_info)
     
     print('\n--------------  get_srl_triple --------------')
     data = hit_ltp.get_srl_triple(s)
     print('words: ', data['words'])
     print('postags: ', data['postags'])
     print('arcs: ', data['arcs'])
     print('ner_info: ', data['ner_info'])
     print('triple_info: ', data['triple_info'])
     
     print('\n--------------  get_parser_triple --------------')
     data = hit_ltp.get_parser_triple(s)
     print('words: ', data['words'])
     print('postags: ', data['postags'])
     print('arcs: ', data['arcs'])
     print('core_words_info: ', data['core_words_info'])
     print('ner_info: ', data['ner_info'])
     print('triple_info: ', data['triple_info'])
     
     
     hit_ltp.release()
     
     
     
     
     
     
     
     