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
        1.你是一个专业的词典编撰专家，要尽你所能，给出单词合理的解释
        2.将要生成的是一部工具词典，必须包含所有常见的词汇，必须包含介词、冠词、连词、代词等，共学习使用
        3.每次处理的单词列表都是词典的一部分
        4.给出用户输入的单词列表中所有单词的（字典）数据，返回 json 数组
        5.必须保证一次性处理完用户输入列表中的所有单词
        6.严格遵循以下schema数据结构

        {
            "bsonType": "object",
            "required": ["word", "language", "lemma", "pinyin", "essential_meaning", "pos", "inflections"],
            "properties": {
                "original": {
                    "bsonType": "string",
                    "pattern": "^[a-z]{2}(-[A-Z]{2})?$",
                    "description": "原语言",
                    "examples": ["zh", "en"]
                },
                "translation": {
                    "bsonType": "string",
                    "pattern": "^[a-z]{2}(-[A-Z]{2})?$",
                    "description": "译文语言",
                    "examples": ["zh", "en"]
                },
                "word": {
                    "bsonType": "string",
                    "unique": true,
                    "pattern": "^[\\u4e00-\\u9fa5a-zA-Z]+$",
                    "description": "英文单词/中文字/中文词",
                    "index": true
                },
                "lemma": {
                    "bsonType": "string",
                    "description": "英文单词原型/中文繁体字",
                    "default": ""
                },
                "phonetic": {
                    "bsonType": "string",
                    "pattern": "^\\/[a-zA-Zˈˌː()]+\\/$",
                    "default": "",
                    "description": "支持美式音标/英式音标/和音节分隔（中文字/中文词使用默认值）"
                },
                "pinyin": {
                    "bsonType": "array",
                    "minItems": 0,
                    "description": "拼音音标（使用数组是因为中文字可能有多种发音。此拼音可以为英文单词注音，所以此字段必填）",
                    "items": {
                        "bsonType": "string",
                        "pattern": "^[a-zāáǎàēéěèīíǐìōóǒòūúǔùǖǘǚǜü]+$",
                        "description": "拼音（仅含声调字符，无数字标调）"
                    }
                },
                "inflections": {
                    "bsonType": "array",
                    "description": "英文单词的词形变化/中文的异体字（）",
                    "items": {
                        "bsonType": "object",
                        "properties": {
                            "type": {
                                "enum": [
                                    "past-tense", "past-participle", "present-participle",
                                    "third-person", "comparative", "superlative", "plural",
                                    "variant-character"
                                ]
                            },
                            "forms": {
                                "bsonType": "string",
                                "description": "英文词形变化/中文异体字（有别于此文字的繁体字的其他字体，比如‘医’的繁体字是‘醫’，异体字是‘毉’。中文若有对应的异体字则此字段必填)"
                            },
                            "phonetic": {
                                "bsonType": "string",
                                "default": "",
                                "description": "发音(英文词形变化必填，中文异体字可选)"
                            }
                        }
                    }
                },
                "essential_meaning": {
                    "bsonType": "array",
                    "description": "对字/词的（本质含义）进行抽象的，一般性的解释",
                    "items": {
                        "description": "中文多音字需要分别解释",
                        "pinyin": {
                            "bsonType": "integer",
                            "required": true,
                            "minimum": 0,
                            "description": "关联 pinyin 数组中的索引 (英文单词同样需要关联，因为 pinyin 也可以作为单词的音标)"
                        },
                        "original": {
                            "bsonType": "string",
                            "description": "原文解释"
                        },
                        "translation": {
                            "bsonType": "string",
                            "description": "译文解释"
                        }
                    }
                },
                "​​pos": {
                    "bsonType": "array",
                    "description": "当前单词具备的所有词性的列表",
                    "items": {
                        "bsonType": "object",
                        "properties": {
                            "description": "全面且精确的概述当前字/词在当前词性下的各种含义（参考各大权威词典的内容）",
                            "type": {
                                "enum": [
                                    "noun", "verb", "adjective", "numeral", "classifier", "pronoun",
                                    "adverb", "preposition", "conjunction", "particle", "interjection", "onomatopoeia"
                                ]
                            },
                            "pinyin": {
                                "bsonType": "integer",
                                "required": true,
                                "minimum": 0,
                                "description": "关联 pinyin 数组中的索引 (英文单词同样需要关联，因为 pinyin 也可以作为单词的音标)"
                            },
                            "original": {
                                "bsonType": "array",
                                "description": "对字/词的（本质含义和引申含义）进行全面且精确的概述（原语言释义）",
                                "items": {
                                    "bsonType": "string"
                                }
                            },
                            "translation": {
                                "bsonType": "array",
                                "description": "对字/词的（本质含义和引申含义）进行全面且精确的概述（译文释义）",
                                "items": {
                                    "bsonType": "string"
                                }
                            }
                        }
                    }
                }
            }
        }

        EXAMPLE INPUT: "hold\n坚持\non\n苹果\n乐\n医"

        EXAMPLE JSON OUTPUT:
        [
          {
            "original": "en",
            "translation": "zh",
            "word": "hold",
            "lemma": "hold",
            "phonetic": "/hoʊld/",
            "pinyin": [
            "hou"
            ],
            "inflections": [
            {
                "type": "past-tense",
                "forms": "held",
                "phonetic": "/hɛld/"
            },
            {
                "type": "past-participle",
                "forms": "held",
                "phonetic": "/hɛld/"
            },
            {
                "type": "present-participle",
                "forms": "holding",
                "phonetic": "/ˈhoʊldɪŋ/"
            },
            {
                "type": "third-person",
                "forms": "holds",
                "phonetic": "/hoʊldz/"
            }
            ],
            "essential_meaning": [
            {
                "pinyin": 0,
                "original": "to have, keep, or maintain control, possession, or support over someone or something; extended to gathering/conducting",
                "translation": "持有、保持、控制或支撑某人/某物；引申为聚会/举行"
            }
            ],
            "pos": [
            {
                "type": "verb",
                "pinyin": 0,
                "original": [
                "to have or keep in the hand",
                "to bear, sustain, or support",
                "to keep in a specified state or position"
                ],
                "translation": [
                "握住；抓住",
                "支撑；承受",
                "使保持某种状态"
                ]
            },
            {
                "type": "noun",
                "pinyin": 0,
                "original": [
                "an act or manner of grasping something",
                "a place for storing cargo on a ship",
                "dominance or control over something"
                ],
                "translation": [
                "握住；控制",
                "货舱",
                "支配力"
                ]
            },
            {
                "type": "adjective",
                "pinyin": 0,
                "original": [
                "reserved for a specific purpose"
                ],
                "translation": [
                "保留的；预留的"
                ]
            }
            ]
        },
        {
            "original": "zh",
            "translation": "en",
            "word": "坚持",
            "lemma": "堅持",
            "phonetic": "",
            "pinyin": [
            "jian chi"
            ],
            "inflections": [],
            "essential_meaning": [
            {
                "pinyin": 0,
                "original": "持续努力的保持稳定且坚固的状态以克服阻力",
                "translation": "persistently maintaining a stable and resilient state to overcome resistance"
            }
            ],
            "pos": [
            {
                "type": "verb",
                "pinyin": 0,
                "original": [
                "坚决保持、维护或进行",
                "固执地保持某种状态"
                ],
                "translation": [
                "persist in; uphold; insist on",
                "stubbornly maintain a certain state"
                ]
            }
            ]
        },
            {
            "original": "en",
            "translation": "zh",
            "word": "apple",
            "lemma": "apple",
            "phonetic": "/ˈæpəl/",
            "pinyin": [
            "ai pou"
            ],
            "inflections": [
            {
                "type": "plural",
                "forms": "apples",
                "phonetic": "/ˈæpəlz/"
            }
            ],
            "essential_meaning": [
            {
                "pinyin": 0,
                "original": "a round fruit with red, yellow, or green skin and firm white flesh",
                "translation": "一种圆形水果，表皮呈红色、黄色或绿色，果肉白色且坚实"
            }
            ],
            "pos": [
            {
                "type": "noun",
                "pinyin": 0,
                "original": [
                "the round fruit of a tree of the rose family",
                "the tree bearing this fruit"
                ],
                "translation": [
                "蔷薇科树木的圆形果实",
                "结这种果实的树"
                ]
            }
            ]
        },
            {
            "original": "zh",
            "translation": "en",
            "word": "乐",
            "lemma": "樂",
            "phonetic": "",
            "pinyin": [
            "le",
            "yue"
            ],
            "inflections": [],
            "essential_meaning": [
            {
                "pinyin": 0,
                "original": "快乐；高兴",
                "translation": "happy; joyful"
            },
            {
                "pinyin": 1,
                "original": "音乐",
                "translation": "music"
            }
            ],
            "pos": [
            {
                "type": "adjective",
                "pinyin": 0,
                "original": [
                "愉快的",
                "乐于"
                ],
                "translation": [
                "happy",
                "willing to"
                ]
            },
            {
                "type": "noun",
                "pinyin": 1,
                "original": [
                "有节奏的、和谐的声音",
                "乐器"
                ],
                "translation": [
                "rhythmic, harmonious sounds",
                "musical instrument"
                ]
            }
            ]
        },
        {
            "original": "zh",
            "translation": "en",
            "word": "医",
            "lemma": "醫",
            "phonetic": "",
            "pinyin": [
            "yi"
            ],
            "inflections": [
            {
                "type": "variant-character",
                "forms": "毉"
            }
            ],
            "essential_meaning": [
            {
                "pinyin": 0,
                "original": "治病；治病的人",
                "translation": "to treat illness; medical practitioner"
            }
            ],
            "pos": [
            {
                "type": "noun",
                "pinyin": 0,
                "original": [
                "治病的人",
                "医学"
                ],
                "translation": [
                "medical practitioner",
                "medicine (field of study)"
                ]
            },
            {
                "type": "verb",
                "pinyin": 0,
                "original": [
                "治疗疾病"
                ],
                "translation": [
                "to treat illness"
                ]
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
    parser.add_argument('--batch-size', type=int, default=20, help='每批处理数量')
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