from pymongo import MongoClient, UpdateOne
from tqdm import tqdm  # 进度条支持

# 连接MongoDB
client = MongoClient("mongodb://localhost:27017/")
db = client["ecdict_db"]
collection = db["words_alpha_only"]

# Exchange类型映射（已删除lemma_transform）
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

def parse_exchange(word, exchange_str):
    """解析exchange字段，生成优化后的inflections结构"""
    inflections = {
        "language": "en",  # 默认英语
        "exchanges": {},
        "lemma": word,
        "is_lemma": True
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
        
        # 处理词形变化
        elif abbrev in EXCHANGE_MAP:
            # 获取变形单词的音标
            variant_doc = collection.find_one({"word": value})
            phonetic = variant_doc.get("phonetic", "") if variant_doc else ""
            
            if phonetic:
                inflections["exchanges"][phonetic] = {
                    "type": EXCHANGE_MAP[abbrev],
                    "forms": value  # 统一使用字符串
                }
    
    return inflections

def update_inflections_batch():
    total = collection.count_documents({})
    batch_size = 1000
    
    with tqdm(total=total, desc="Processing") as pbar:
        for i in range(0, total, batch_size):
            # 获取批次数据
            cursor = collection.find({}).skip(i).limit(batch_size)
            batch = list(cursor)
            
            if not batch:
                break
            
            # 准备批量操作
            bulk_ops = []
            for doc in batch:
                # 跳过非字母开头的单词（双重保险）
                if not doc["word"][0].isalpha():
                    continue
                
                # 生成新的inflections结构
                new_inflections = parse_exchange(doc["word"], doc.get("exchange", ""))
                
                bulk_ops.append(
                    UpdateOne(
                        {"_id": doc["_id"]},
                        {"$set": {"inflections": new_inflections}}
                    )
                )
            
            # 执行批量写入
            if bulk_ops:
                collection.bulk_write(bulk_ops, ordered=False)
            
            pbar.update(len(batch))

# 执行更新
update_inflections_batch()

# 创建优化后的索引
collection.create_index("inflections.exchanges")
collection.create_index("inflections.lemma")
collection.create_index([
    ("inflections.exchanges.type", 1),
    ("inflections.exchanges.forms", 1)
])

print("优化后的inflections字段更新完成！")