import re
import json
import enchant
from nltk.corpus import wordnet
from collections import OrderedDict
from tqdm import tqdm  # 用于显示进度条

contractions = [
    # ====== 动词否定形式 (Verb Negations) ======
    "isn't",    # 原型: "is not"     示例: "She isn't here."
    "aren't",   # 原型: "are not"    示例: "They aren't ready."
    "wasn't",   # 原型: "was not"    示例: "It wasn't funny."
    "weren't",  # 原型: "were not"   示例: "We weren't invited."
    "don't",    # 原型: "do not"     示例: "I don't know."
    "doesn't",  # 原型: "does not"   示例: "He doesn't care."
    "didn't",   # 原型: "did not"    示例: "They didn't come."
    "haven't",  # 原型: "have not"   示例: "I haven't finished."
    "hasn't",   # 原型: "has not"    示例: "She hasn't called."
    "hadn't",   # 原型: "had not"    示例: "He hadn't seen it."
    "can't",    # 原型: "cannot"     示例: "You can't enter."
    "couldn't", # 原型: "could not"  示例: "I couldn't sleep."
    "won't",    # 原型: "will not"   示例: "It won't happen."
    "wouldn't", # 原型: "would not"  示例: "She wouldn't agree."
    "shouldn't",# 原型: "should not" 示例: "You shouldn't do that."
    "mustn't",  # 原型: "must not"   示例: "You mustn't tell."

    # ====== 动词缩略形式 (Verb Contractions) ======
    "I'm",      # 原型: "I am"       示例: "I'm tired."
    "you're",   # 原型: "you are"    示例: "You're right."
    "he's",     # 原型: "he is/has"  示例: "He's busy." / "He's gone."
    "she's",    # 原型: "she is/has" 示例: "She's a doctor." / "She's finished."
    "it's",     # 原型: "it is/has"  示例: "It's raining." / "It's been hours."
    "we're",    # 原型: "we are"     示例: "We're late."
    "they're",  # 原型: "they are"   示例: "They're coming."
    "I've",     # 原型: "I have"     示例: "I've seen it."
    "you've",   # 原型: "you have"   示例: "You've changed."
    "we've",    # 原型: "we have"    示例: "We've decided."
    "they've",  # 原型: "they have"  示例: "They've left."
    "I'd",      # 原型: "I had/would"示例: "I'd already eaten." / "I'd like to go."
    "you'd",    # 原型: "you had/would" 示例: "You'd better run." / "You'd prefer tea."

    # ====== 特殊固定搭配 (Special Cases) ======
    "let's",    # 原型: "let us"     示例: "Let's go."
    "o'clock",  # 原型: "of the clock" 示例: "It's 3 o'clock."

    # ====== 标点型缩略 (Punctuation Shortcuts) ======
    "'70s",     # 原型: "1970s"      示例: "Music from the '70s"
    "gov't",    # 原型: "government" 示例: "Gov't officials"
    "int'l"     # 原型: "international" 示例: "Int'l standards"
]

# 排除列表（非标准/易混淆）
excluded = [
    "ain't", "gonna", "wanna", "gotta", "kinda",
    "outta", "gimme", "'cause", "'twas", "o'er",
    "ne'er", "e'en", "y'all"
]

def classify_words_to_json(input_file, output_alpha_json, output_non_alpha_json):
    alpha_words = OrderedDict()  # 用 OrderedDict 保持顺序并去重
    non_alpha_words = OrderedDict()

    with open(input_file, 'r', encoding='utf-8') as infile:
        for line in infile:
            parts = line.strip().split()
            if len(parts) >= 2:  # 确保至少有数字和单词
                word = parts[1]  # 单词在第 2 列
                if re.fullmatch(r'^[a-zA-Z]+$', word):
                    alpha_words[word] = None  # 使用字典键去重
                else:
                    non_alpha_words[word] = None

    # 提取去重后的单词列表（保持顺序）
    alpha_words_list = list(alpha_words.keys())
    non_alpha_words_list = list(non_alpha_words.keys())

    word_set = set()
    try:
        print("正在加载WordNet词汇...")
        wn_words = set()
        for synset in tqdm(wordnet.all_synsets(), desc="处理WordNet"):
            for lemma in synset.lemmas():
                wn_words.add(lemma.name().lower().replace('_', ' '))
        word_set.update(wn_words)
        print(f"从WordNet添加了 {len(wn_words)} 个单词")
    except Exception as e:
        print(f"无法加载WordNet: {e}")

    # 转换为列表并排序
    all_words = sorted(word_set)

    print("使用PyEnchant验证单词...")
    enchant_dict = enchant.Dict("en_US")
    valid_words = []
    for word in tqdm(alpha_words_list, desc="验证单词"):
        if enchant_dict.check(word):
            valid_words.append(word)
    print(f"PyEnchant验证后保留 {len(valid_words)}/{len(alpha_words_list)} 个单词")

    alpha_words = {}

    for lemma in valid_words:
        alpha_words[lemma] = None

    pattern = r'^[^a-zA-Z].*$'
    # pattern = r'^[0-9.].*$'
    # pattern = r'^.*[0-9.].*$'
    for word in all_words:
        if not re.fullmatch(pattern, word):
            alpha_words[word] = None  # 使用字典键去重
        else:
            non_alpha_words[word] = None

    alpha_words_list = list(alpha_words.keys())
    alpha_words_list += contractions

    # 保存为 JSON 文件
    with open(output_alpha_json, 'w', encoding='utf-8') as alpha_file:
        json.dump(alpha_words_list, alpha_file, indent=4, ensure_ascii=False)

    with open(output_non_alpha_json, 'w', encoding='utf-8') as non_alpha_file:
        json.dump(non_alpha_words_list, non_alpha_file, indent=4, ensure_ascii=False)

# 使用示例
input_file = 'all.num.o5'
output_alpha_json = 'wordlist.json'
output_non_alpha_json = 'non_alpha_words.json'

classify_words_to_json(input_file, output_alpha_json, output_non_alpha_json)