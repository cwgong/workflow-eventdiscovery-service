# -*- coding: utf-8 -*-

'''
import codecs
import json
import io


original_data_file = 'logs/original_data.txt'

new_file_data = []
old_ids = []
c = 0

new_file_data = []
old_ids = []

with io.open(original_data_file, 'r', encoding='utf-8') as f: 
    while True:
        line = f.readline()
        if len(line) > 0:
            try:
                json_data = json.loads(line)
            except:
                continue
            old_ids.append(json_data['id'])
        else:
            break
    
print("old_ids: {}".format(len(old_ids)))
print(c)
'''

a = [1,2,3,4,5]
print(max(a))