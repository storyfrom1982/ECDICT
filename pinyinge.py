import json
import argparse
from pathlib import Path
from typing import List, Dict, Optional
from pymongo import MongoClient
from openai import OpenAI

class PinyinProcessor:
    def __init__(
        self,
        api_key: str,
        mongo_uri: str = "mongodb://localhost:27017/",
        db_name: str = "pinyin_db",
        collection_name: str = "pinyinge-words"
    ):
        self.client = OpenAI(
            api_key=api_key,
            base_url="https://api.deepseek.com"
        )
        self.mongo = MongoClient(mongo_uri)
        self.collection = self.mongo[db_name][collection_name]
        self.collection.create_index("word", unique=True)

    def process_words(self, words: List[str]) -> Optional[List[Dict]]:
        """处理单词列表并返回解析后的数据（失败返回None）"""
        if not words:
            return []

        system_prompt = """
        请遵循以下schema数据表结构：
        {
            "bsonType": "object",
            "required": ["word", "stem", "pinyin", "phonetic", "meaning", "pos", "lemma"],
            "properties": {
                "word": {
                    "bsonType": "string",
                    "description": "英文单词/中文字/中文词",
                    "unique": true,
                    "pattern": "^[\\u4e00-\\u9fa5a-zA-Z]+$",
                    "index": true
                },
                "​stem": {
                    "bsonType": "string",
                    "description": "英文单词的词根；中文汉字的偏旁部首；中文词使用主导词性的那个汉字；"
                },
                "lemma": {
                    "bsonType": "string",
                    "description": "英文单词原型/中文繁体字"
                },
                "phonetic": {
                    "bsonType": "string",
                    "description": "国际音标",
                    "pattern": "^\\/([a-zA-Zˈˌː()]+\\/)?$",
                    "default": ""
                },
                "pinyin": {
                    "bsonType": "array",
                    "minItems": 0,
                    "description": "拼音（使用数组是需要支持中文多音字）",
                    "items": {
                        "bsonType": "string",
                        "description": "拼音，中文词的每个字要单独占一个数组元素（仅含声调字符，禁止数字标调）",
                        "pattern": "^[a-zāáǎàēéěèīíǐìōóǒòūúǔùǖǘǚǜü]+$",
                        "default": ""
                    }
                },
                "pos": {
                    "bsonType": "array",
                    "description": "此中文汉字或英文单词具备的所有词性的列表",
                    "items": {
                        "bsonType": "object",
                        "properties": {
                            "type": {
                                "enum": [
                                    "noun", "verb", "adjective", "numeral", "classifier", "pronoun",
                                    "adverb", "preposition", "conjunction", "particle", "interjection", "onomatopoeia"
                                ]
                            },
                            "pinyin": {
                                "bsonType": "integer",
                                "description": "关联 pinyin 数组中的索引，中文多音字必须关联对应的拼音",
                                "required": true,
                                "minimum": 0
                            },
                            "meaning": {
                                "bsonType": "object",
                                "description": "当前词性对应的本意",
                                "required": true,
                                "properties": {
                                    "original": {
                                        "bsonType": "string",
                                        "description": "对本意进行全面且精确的概述；使用原文（单词用英文，汉字用中文）"
                                    },
                                    "translation": {
                                        "bsonType": "string",
                                        "description": "对应的翻译"
                                    }
                                }
                            },
                            "figurative": {
                                "bsonType": "array",
                                "description": "当前词性对应的所有引申含义",
                                "required": true,
                                "items": {
                                    "bsonType": "object",
                                    "properties": {
                                        "original": {
                                            "bsonType": "string",
                                            "description": "对引申含义进行全面且精确的概述，使用原文（单词用英文，汉字用中文）"
                                        },
                                        "translation": {
                                            "bsonType": "string",
                                            "description": "对应的翻译"
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
        输出列表中所有单词对应的数据，输出为 json 格式
        我需要你帮我收集所有常用词汇的对应数据，我的目的是收集和整理

        EXAMPLE INPUT: "hold\n坚持\non\n苹果\n乐\n医"

        EXAMPLE JSON OUTPUT:
        [
            {
                "word": "hold",
                "stem": "hold",
                "lemma": "hold",
                "phonetic": "/həʊld/",
                "pinyin": [],
                "pos": [
                {
                    "type": "verb",
                    "pinyin": 0,
                    "meaning": {
                    "original": "to have or keep in the hand; keep fast; grasp",
                    "translation": "握住；持有"
                    },
                    "figurative": [
                    {
                        "original": "to keep in the mind",
                        "translation": "持有（观点）"
                    },
                    {
                        "original": "to contain or be capable of containing",
                        "translation": "容纳"
                    }
                    ]
                },
                {
                    "type": "noun",
                    "pinyin": 0,
                    "meaning": {
                    "original": "an act or manner of grasping something",
                    "translation": "握住；控制"
                    },
                    "figurative": []
                }
                ]
            },
            {
                "word": "坚持",
                "stem": "坚",
                "lemma": "堅持",
                "phonetic": "",
                "pinyin": ["jiān", "chí"],
                "pos": [
                {
                    "type": "verb",
                    "pinyin": 0,
                    "meaning": {
                    "original": "坚决保持、维护或进行",
                    "translation": "persist in; insist on"
                    },
                    "figurative": []
                }
                ]
            },
            {
                "word": "on",
                "stem": "on",
                "lemma": "on",
                "phonetic": "/ɒn/",
                "pinyin": [],
                "pos": [
                {
                    "type": "preposition",
                    "pinyin": 0,
                    "meaning": {
                    "original": "in contact with and supported by (a surface)",
                    "translation": "在...上"
                    },
                    "figurative": [
                    {
                        "original": "about; concerning",
                        "translation": "关于"
                    }
                    ]
                },
                {
                    "type": "adverb",
                    "pinyin": 0,
                    "meaning": {
                    "original": "physically in contact with and supported by a surface",
                    "translation": "在上"
                    },
                    "figurative": []
                }
                ]
            },
            {
                "word": "苹果",
                "stem": "苹",
                "lemma": "蘋果",
                "phonetic": "",
                "pinyin": ["píng", "guǒ"],
                "pos": [
                {
                    "type": "noun",
                    "pinyin": 0,
                    "meaning": {
                    "original": "一种常见的水果",
                    "translation": "apple"
                    },
                    "figurative": []
                }
                ]
            },
            {
                "word": "乐",
                "stem": "丿",
                "lemma": "樂",
                "phonetic": "",
                "pinyin": ["lè", "yuè"],
                "pos": [
                {
                    "type": "adjective",
                    "pinyin": 0,
                    "meaning": {
                    "original": "快乐；高兴",
                    "translation": "happy; joyful"
                    },
                    "figurative": []
                },
                {
                    "type": "noun",
                    "pinyin": 1,
                    "meaning": {
                    "original": "音乐",
                    "translation": "music"
                    },
                    "figurative": []
                }
                ]
            }
        ]
        """

        try:
            response = self.client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": "\n".join(words)}
                ],
                response_format={"type": "json_object"}
            )
            return self._parse_response(response.choices[0].message.content)
        except Exception as e:
            print(f"API请求失败: {str(e)}")
            return None

    def _parse_response(self, raw: str) -> List[Dict]:
        """解析API响应"""
        print(f"ret=======>>>{raw}")
        try:
            if "```json" in raw:
                raw = raw.split("```json")[1].split("```")[0].strip()
            data = json.loads(raw)
            return data if isinstance(data, list) else [data]
        except json.JSONDecodeError as e:
            print(f"JSON解析失败: {str(e)}\n原始响应:\n{raw[:200]}...")
            return []

    def save_to_mongo(self, data: List[Dict]) -> int:
        """保存到MongoDB并返回成功数量"""
        if not data:
            return 0

        success = 0
        for item in data:
            try:
                result = self.collection.update_one(
                    {"word": item["word"]},
                    {"$set": item},
                    upsert=True
                )
                if result.upserted_id or result.modified_count > 0:
                    success += 1
            except Exception as e:
                print(f"保存失败 {item.get('word')}: {str(e)}")
        return success

    def close(self):
        self.mongo.close()

class BatchProcessor:
    def __init__(self, api_key: str, word_file: str, progress_file: str = ".progress"):
        self.processor = PinyinProcessor(api_key)
        self.word_file = Path(word_file)
        self.progress_file = Path(progress_file)
        self.processed = self._load_progress()

    def run(self, batch_size: int = 20, test_mode: bool = False):
        """执行批处理
        :param test_mode: 测试模式下只处理一个批次
        """
        words = self._load_words()
        pending = [w for w in words if w not in self.processed]
        
        print(f"总单词: {len(words)}, 待处理: {len(pending)}")
        
        batches = min(1, len(pending)) if test_mode else len(pending)
        for i in range(0, batches, batch_size):
            batch = pending[i:i + batch_size]
            print(f"\n处理批次 {i//batch_size + 1}: {batch}")
            
            data = self.processor.process_words(batch)
            print(f"返回结果: {data}")
            if data:
                retlist = {}
                retlist = data[0]
                keys = list(retlist.keys())
                print(f"返回结果 keys: {keys}")
                saved = self.processor.save_to_mongo(retlist[keys[0]])
                print(f"解析结果: 共 {len(data)} 条, 成功保存 {saved} 条")
                print("首条数据示例:", json.dumps(data[0], indent=2, ensure_ascii=False))
                
                if not test_mode:  # 测试模式不更新进度
                    self._update_progress(batch)
            else:
                print("本批次处理失败")

            if test_mode:  # 测试模式只处理一个批次
                print("\n测试模式已停止")
                break

    def _load_words(self) -> List[str]:
        with open(self.word_file, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _load_progress(self) -> set:
        if self.progress_file.exists():
            with open(self.progress_file, 'r') as f:
                return set(json.load(f))
        return set()

    def _update_progress(self, words: List[str]):
        self.processed.update(words)
        with open(self.progress_file, 'w') as f:
            json.dump(list(self.processed), f)

    def close(self):
        self.processor.close()

def main():
    parser = argparse.ArgumentParser(description='拼音数据批处理器')
    parser.add_argument('--api-key', required=True, help='DeepSeek API密钥')
    parser.add_argument('--word-file', default='wordlist.json', help='单词列表JSON文件')
    parser.add_argument('--progress-file', default='.progress', help='进度记录文件')
    parser.add_argument('--batch-size', type=int, default=10, help='每批处理数量')
    parser.add_argument('--test', action='store_true', help='测试模式（只处理一个批次）')
    args = parser.parse_args()

    processor = BatchProcessor(
        api_key=args.api_key,
        word_file=args.word_file,
        progress_file=args.progress_file
    )
    
    try:
        processor.run(
            batch_size=args.batch_size,
            test_mode=args.test
        )
    finally:
        processor.close()

if __name__ == "__main__":
    main()