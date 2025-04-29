import pandas as pd
from pymongo import MongoClient

# 配置 MongoDB 连接
client = MongoClient("mongodb://localhost:27017/")  # 默认本地端口
db = client["ecdict_db"]  # 数据库名
collection = db["words"]  # 集合名

# 读取 ecdict.csv 文件
csv_path = "ecdict.csv"  # 替换为你的实际路径
df = pd.read_csv(csv_path)

# 清理空值（MongoDB 不存储 NaN）
df = df.where(pd.notnull(df), None)

# 转换为字典列表（适合插入 MongoDB）
data = df.to_dict("records")

# 批量插入数据
batch_size = 10000
for i in range(0, len(data), batch_size):
    collection.insert_many(data[i:i+batch_size])

print(f"导入完成！共插入 {len(data)} 条数据。")