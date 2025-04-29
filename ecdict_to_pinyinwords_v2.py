import csv
import re
from pymongo import MongoClient
from datetime import datetime

def convert_ecdict_to_pinyinwords(csv_file, mongo_uri, db_name):
    client = MongoClient(mongo_uri)
    db = client[db_name]
    collection = db['pinyin-words']
    
    batch_size = 1000
    batch = []
    
    # 词性正则表达式（匹配类似 "vt.", "n.", "adj." 等）
    pos_pattern = re.compile(r'^([a-z]+)\.\s*(.*)$', re.IGNORECASE)
    
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        
        for row in reader:
            word_doc = {
                '_id': row['word'].lower(),
                'word': row['word'],
                'language': 'en',
                'phonetic': format_phonetic(row['phonetic']),
                'version_number': 0,
                'version_list': [{
                    'editor': 'pinyinge',
                    'updated': datetime.utcnow(),
                    'changelog': '从ECDICT导入初始版本'
                }]
            }
            
            # 处理lemma
            if row['exchange']:
                for item in row['exchange'].split('/'):
                    if item.startswith('0:'):
                        word_doc['lemma'] = item[2:]
                        break
            
            # 从translation提取词性和释义
            if row['translation']:
                pos_entries = process_translation(row['translation'])
                if pos_entries:
                    word_doc['pos'] = pos_entries
            
            # 处理变形词
            if row['exchange']:
                word_doc['inflections'] = process_inflections(row['exchange'])
            
            # 处理标签
            word_doc['tags'] = process_tags(row)
            
            batch.append(word_doc)
            
            if len(batch) >= batch_size:
                collection.insert_many(batch)
                batch = []
                print(f'已导入 {collection.count_documents({})} 条记录')
    
    if batch:
        collection.insert_many(batch)
        print(f'最终导入 {collection.count_documents({})} 条记录')

def process_translation(translation):
    """从translation字段提取词性和释义"""
    pos_map = {
        'vt': 'verb',
        'vi': 'verb',
        'v': 'verb',
        'n': 'noun',
        'adj': 'adjective',
        'adv': 'adverb',
        'prep': 'preposition',
        'conj': 'conjunction',
        'pron': 'pronoun',
        'interj': 'interjection',
        'num': 'numeral',
        'art': 'article',
        'aux': 'auxiliary'
    }
    
    pos_entries = {}
    lines = [line.strip() for line in translation.split('\\n') if line.strip()]
    
    for line in lines:
        # 匹配词性缩写和释义
        match = re.match(r'^([a-z]+)\.\s*(.*)$', line, re.IGNORECASE)
        if match:
            pos_abbr, definitions = match.groups()
            pos_type = pos_map.get(pos_abbr.lower(), 'other')
            
            # 分割多个释义
            defs = [d.strip() for d in definitions.split(',') if d.strip()]
            
            if pos_type in pos_entries:
                pos_entries[pos_type].extend(defs)
            else:
                pos_entries[pos_type] = defs
    
    # 转换为pinyin-words所需的格式
    result = []
    for pos_type, translations in pos_entries.items():
        result.append({
            'type': pos_type,
            'translations': translations
        })
    
    return result

def process_inflections(exchange):
    """处理词形变化"""
    exchange_map = {
        'p': 'past-tense',
        'd': 'past-participle',
        'i': 'present-participle',
        '3': 'third-person',
        'r': 'comparative',
        't': 'superlative',
        's': 'plural'
    }
    
    inflections = []
    for item in exchange.split('/'):
        if ':' in item and item[0] in exchange_map:
            inflection_type = exchange_map[item[0]]
            inflection_form = item[2:]
            
            inflections.append({
                'type': inflection_type,
                'forms': inflection_form
            })
    
    return inflections

def process_tags(row):
    """生成标签列表"""
    tags = []
    if row['tag']:
        tags.extend(row['tag'].split())
    if row['collins'] and int(row['collins']) > 0:
        tags.append(f'collins{row["collins"]}')
    if row['oxford'] == '1':
        tags.append('oxford3000')
    if row['bnc']:
        tags.append(f'bnc{row["bnc"]}')
    if row['frq']:
        tags.append(f'frq{row["frq"]}')
    return tags

def format_phonetic(phonetic):
    """格式化音标"""
    if not phonetic:
        return None
    if not phonetic.startswith('/'):
        phonetic = '/' + phonetic
    if not phonetic.endswith('/'):
        phonetic = phonetic + '/'
    return phonetic

if __name__ == '__main__':
    # 配置参数
    ECDICT_CSV = 'ecdict.csv'
    MONGO_URI = 'mongodb://localhost:27017/'
    DB_NAME = 'pinyin-dict'
    
    # 执行导入
    convert_ecdict_to_pinyinwords(ECDICT_CSV, MONGO_URI, DB_NAME)