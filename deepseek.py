import json
from openai import OpenAI

client = OpenAI(
    api_key="your API key",
    base_url="https://api.deepseek.com",
)

system_prompt = """
// 请遵循于以下数据结构：
// pinyin-words.schema.json
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
// 输出以下单词列表中每个单词的（字典）数据，返回 json list。请尽你所能，给出合理的数据。

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

user_prompt = "the\n长\napple\nmake\n重"

messages = [{"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}]

response = client.chat.completions.create(
    model="deepseek-chat",
    messages=messages,
    response_format={
        'type': 'json_object'
    }
)

print(json.loads(response.choices[0].message.content))