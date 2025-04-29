from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017/")
db = client["ecdict_db"]

# 筛选条件：word 字段以字母开头
query = {
    "word": { "$regex": r"^[A-Za-z]" }  # 正则表达式
}

# 将结果写入新集合
db["words"].aggregate([
    {"$match": query},
    {"$out": "words_alpha_only"}
])

print("导出完成！")