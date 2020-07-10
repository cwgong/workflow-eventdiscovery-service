# -*- coding: utf-8 -*-

def fetch_data(text_file):
    print('text_file: ', text_file)
    temp_ners = []
    stop_words = load_stop_words()
    
    # 过滤掉「偏公司行业经济类」资讯
    political_title_supervision = Political_Title_Supervision()
    
    _ner_data = []
    _word_data = []
    _text_data = []
    _title_word_data = []
    _raw_data = []
    p_count = 0
    n_count = 0
    with io.open(text_file, "r", encoding='utf-8') as f:
        while True:
            line = f.readline()
            if len(line) > 0:
                json_data = json.loads(line)
                if 'title' in json_data and 'content' in json_data:
                    logger.info(json_data['title'] + ' ' + str(political_title_supervision.f(json_data['title'])))
                    if political_title_supervision.f(json_data['title']):
                        p_count += 1
                        title_ner = [term['word'] for term in json_data['seg_title'] if term['ner'] != 'O' or term['word'] in temp_ners]
                        content_ner = [term['word'] for term in json_data['seg_content'] if term['ner'] != 'O' or term['word'] in temp_ners]
                        content_ner.extend(title_ner)
                        _ner_data.append(content_ner)
                        t_w = [term['word'] for term in json_data['seg_title'] if
                               term['word'] not in stop_words and term['nature'].startswith('n') or term['nature'].startswith('v')]
                        c_w = [term['word'] for term in json_data['seg_content'] if
                               term['word'] not in stop_words and term['nature'].startswith('n') or term['nature'].startswith('v')]
                        c_w.extend(t_w)
                        _title_word_data.append(t_w)
                        _word_data.append(c_w)
                        _text_data.append(json_data['title'] + ' ' +json_data['content'])
                        json_data.pop('seg_title')
                        json_data.pop('seg_content')
                        json_data['ners'] = content_ner
                        json_data['words'] = c_w
                        json_data['title_words'] = t_w
                        json_data['text'] = json_data['title'] + ' ' +json_data['content']
                        _raw_data.append(json_data)
                    else:
                        n_count += 1
            else:
                break
    
    logger.info("fetch_data p_count: {}".format(p_count))
    logger.info("fetch_data n_count: {}".format(n_count))
    return _ner_data, _word_data, _text_data, _title_word_data, _raw_data