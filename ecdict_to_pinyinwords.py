import csv
import json
from pymongo import MongoClient
from datetime import datetime

def convert_ecdict_to_pinyinwords(csv_file, mongo_uri, db_name):
    # MongoDB连接
    client = MongoClient(mongo_uri)
    db = client[db_name]
    collection = db['pinyin-words']
    
    # 批量插入缓冲区
    batch_size = 1000
    batch = []
    
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        
        for row in reader:
            # 基础字段映射
            word_doc = {
                '_id': row['word'].lower(),  # 使用小写单词作为ID
                'word': row['word'],
                'language': 'en',
                'phonetic': row['phonetic'],
                'version_number': 0,
                'version_list': [{
                    'editor': 'pinyinge',
                    'updated': datetime.utcnow(),
                    'changelog': '从ECDICT导入初始版本'
                }]
            }
            
            # 处理lemma (通过exchange字段)
            if row['exchange']:
                for item in row['exchange'].split('/'):
                    if item.startswith('0:'):
                        word_doc['lemma'] = item[2:]
                        break
            
            # 处理词性 (POS)
            if row['pos']:
                pos_entries = []
                for pos_pair in row['pos'].split('/'):
                    if ':' in pos_pair:
                        pos_type, percent = pos_pair.split(':')
                        pos_entries.append({
                            'type': convert_pos(pos_type),
                            'translations': row['translation'].split('\\n') if row['translation'] else []
                        })
                if pos_entries:
                    word_doc['pos'] = pos_entries
            
            # 处理变形词 (inflections)
            if row['exchange']:
                inflections = []
                exchange_map = {
                    'p': 'past-tense',
                    'd': 'past-participle',
                    'i': 'present-participle',
                    '3': 'third-person',
                    'r': 'comparative',
                    't': 'superlative',
                    's': 'plural'
                }
                
                for item in row['exchange'].split('/'):
                    if ':' in item and item[0] in exchange_map:
                        inflection_type = exchange_map[item[0]]
                        inflection_form = item[2:]
                        
                        inflections.append({
                            'type': inflection_type,
                            'forms': inflection_form
                        })
                
                if inflections:
                    word_doc['inflections'] = inflections
            
            # 处理标签 (tags)
            tags = []
            if row['tag']:
                tags.extend(row['tag'].split())
            if row['collins'] and int(row['collins']) > 0:
                tags.append(f'collins{row["collins"]}')
            if row['oxford'] == '1':
                tags.append('oxford3000')
            
            if tags:
                word_doc['tags'] = tags
            
            # 添加到批量缓冲区
            batch.append(word_doc)
            
            # 批量插入
            if len(batch) >= batch_size:
                collection.insert_many(batch)
                batch = []
                print(f'已导入 {collection.count_documents({})} 条记录')
    
    # 插入剩余记录
    if batch:
        collection.insert_many(batch)
        print(f'最终导入 {collection.count_documents({})} 条记录')

def convert_pos(ecdict_pos):
    pos_mapping = {
        'n': 'noun',
        'v': 'verb',
        'a': 'adjective',
        'ad': 'adverb',
        'c': 'conjunction',
        'p': 'preposition',
        'u': 'auxiliary',
        'pr': 'pronoun',
        'num': 'numeral',
        'int': 'interjection',
        'phr': 'phrase',
        'pref': 'prefix',
        'suf': 'suffix'
    }
    return pos_mapping.get(ecdict_pos, 'other')

if __name__ == '__main__':
    # 配置参数
    ECDICT_CSV = 'ecdict.csv'
    MONGO_URI = 'mongodb://localhost:27017/'
    DB_NAME = 'pinyin-dictionary'
    
    # 执行导入
    convert_ecdict_to_pinyinwords(ECDICT_CSV, MONGO_URI, DB_NAME)