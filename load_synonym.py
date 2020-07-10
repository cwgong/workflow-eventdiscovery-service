# -*- coding: utf-8 -*-

import io

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
    
    
    file_path = './CoreSynonym.txt'
    
    synonym_info = load_synonym(file_path)
    
    print(synonym_info['发出'])
    print(synonym_info['说'])
    
    
    
    