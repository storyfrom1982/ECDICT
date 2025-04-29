from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017/")
db = client["ecdict_db"]

# 筛选条件：frq ≠ 0 或 bnc ≠ 0
query = {
    "$or": [
        {"frq": {"$ne": 0}},
        {"bnc": {"$ne": 0}}
    ]
}

# 将结果写入新集合
db["words"].aggregate([
    {"$match": query},
    {"$out": "words_with_frequency"}
])

print("导出完成！")