import json
import csv

def convert_ecdict_to_schema(csv_path, output_json):
    """
    将ECDict CSV数据转换为符合Schema的JSON格式（仅处理英文单词）
    :param csv_path: ECDict CSV文件路径
    :param output_json: 输出JSON文件路径
    """
    result = []
    
    with open(csv_path, 'r', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        
        for row in reader:
            entry = process_english_entry(row)
            if entry:
                result.append(entry)
    
    # 写入JSON文件
    with open(output_json, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

def process_english_entry(row):
    """处理单个英文词条"""
    word = row['word'].strip()
    if not word:
        return None
    
    # 处理原始英文释义中的换行符
    english = row.get('definition', '').replace('\\n', '\n').strip()
    # 处理中文释义中的换行符
    chinese = row.get('translation', '').replace('\\n', '\n').strip()
    
    return {
        "word": word,
        "lemma": get_lemma(row),
        "phonetic": row.get('phonetic', '').strip(),
        "pinyin": [],
        "meaning": [{
            "pinyin": 0,
            "english": english,
            "chinese": chinese
        }]
    }

def get_lemma(row):
    """获取英文单词的原型"""
    # 优先使用exchange字段中的lemma信息
    if 'exchange' in row:
        for item in row['exchange'].split('/'):
            if item.startswith('0:'):
                return item[2:]
    
    # 其次使用sw字段（strip word）
    if 'sw' in row and row['sw'].strip():
        return row['sw'].strip()
    
    # 默认返回单词本身
    return row['word'].strip()

if __name__ == "__main__":
    # 使用示例
    convert_ecdict_to_schema("ecdict.csv", "ecdict_english.json")