from pymongo import MongoClient
from pymongo import UpdateOne  # 导入UpdateOne操作类

# 连接MongoDB
client = MongoClient("mongodb://localhost:27017/")
db = client["ecdict_db"]  # 数据库名
collection = db["words_alpha_only"]  # 目标集合

# Exchange类型到字段名的映射
EXCHANGE_MAP = {
    "p": "past_tense",
    "d": "past_participle",
    "i": "present_participle",
    "3": "third_person",
    "r": "comparative",
    "t": "superlative",
    "s": "plural",
    "0": "lemma"
}

import re

def parse_definition(definition, translation):
    definitions = {}
    if not definition:
        return definitions
    
    # 分割不同词性的解释
    items = definition.split('\n')
    zh_items = translation.split('\n')

    pattern = r'(?:^|(?<=\n))[a-z]\. .*?(?=\n|$)'
    
    for item in items:
        # 匹配词性和解释
        match = re.match(pattern, item)
        if match:
            pos = match.group(1).strip()
            explanation = match.group(2).strip()
            
            # 分离中英文解释（如果有）
            en_zh = explanation.split('//')
            en = en_zh[0].strip() if len(en_zh) > 0 else ''
            zh = en_zh[1].strip() if len(en_zh) > 1 else ''
            
            definitions[pos][en].ap = en
            definitions.append({
                'pos': pos,
                'en': en,
                'zh': zh
            })
    
    return definitions

def parse_exchange(word, exchange_str):
    """解析exchange字段，生成inflections结构"""
    inflections = {
        "types": {},
        "lemma": word,  # 默认lemma是单词本身
        "is_lemma": True  # 默认是lemma
    }
    
    if not exchange_str:
        return inflections
    
    for part in exchange_str.split("/"):
        if ":" not in part:
            continue
        
        abbrev, value = part.split(":", 1)
        
        # 处理lemma(0)
        if abbrev == "0":
            inflections["lemma"] = value
            inflections["is_lemma"] = (value == word)
        elif abbrev in EXCHANGE_MAP:
            inflections["types"][EXCHANGE_MAP[abbrev]] = value
    
    return inflections

# 批量更新所有文档
def update_inflections(batch_size=1000):
    total = collection.count_documents({})
    processed = 0
    
    while processed < total:
        # 分批获取文档
        cursor = collection.find({}).skip(processed).limit(batch_size)
        batch = list(cursor)
        
        if not batch:
            break
            
        # 准备批量操作
        bulk_operations = []
        for doc in batch:
            word = doc["word"]
            exchange = doc.get("exchange", "")
            definition = doc.get("exchange", "")
            
            # 生成inflections字段
            inflections = parse_exchange(word, exchange)

            definitions = parse_definition(definition)
            
            # 创建UpdateOne操作
            bulk_operations.append(
                UpdateOne(
                    {"_id": doc["_id"]},
                    {"$set": {"inflections": inflections}}
                )
            )
        
        # 执行批量操作
        if bulk_operations:
            collection.bulk_write(bulk_operations, ordered=False)
        
        processed += len(batch)
        print(f"已处理 {processed}/{total} 条文档 ({processed/total:.1%})")

# 执行更新
update_inflections()

# 创建索引
collection.create_index("inflections.lemma")
collection.create_index("inflections.types.past_tense")
collection.create_index("inflections.types.plural")

print("inflections字段添加完成！")