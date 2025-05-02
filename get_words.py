import json
import enchant
from nltk.corpus import words, wordnet
from tqdm import tqdm  # 用于显示进度条
from collections import defaultdict

def get_all_words():
    """获取所有来源的单词并合并去重"""
    word_set = set()
    
    # 1. 从NLTK words语料库获取
    try:
        print("正在加载NLTK words语料库...")
        nltk_words = set(w.lower() for w in words.words())
        word_set.update(nltk_words)
        print(f"从NLTK words添加了 {len(nltk_words)} 个单词")
    except Exception as e:
        print(f"无法加载NLTK words: {e}")

    # 2. 从WordNet获取
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

    # 3. 从PyEnchant获取 (英语词典)
    try:
        print("正在检查PyEnchant词典...")
        enchant_dict = enchant.Dict("en_US")
        # PyEnchant没有直接获取所有单词的方法，所以我们只能用它来验证
        # 这里我们可以用它来验证我们已有的单词
        print("PyEnchant将用于验证，但不直接添加单词")
    except Exception as e:
        print(f"无法初始化PyEnchant: {e}")
        enchant_dict = None

    # 转换为列表并排序
    all_words = sorted(word_set)
    
    # 如果需要用PyEnchant过滤
    if enchant_dict:
        print("使用PyEnchant验证单词...")
        valid_words = []
        for word in tqdm(all_words, desc="验证单词"):
            if enchant_dict.check(word):
                valid_words.append(word)
        print(f"PyEnchant验证后保留 {len(valid_words)}/{len(all_words)} 个单词")
        all_words = valid_words

    return all_words

def save_words_to_json(word_list, filename="english_words.json"):
    """将单词列表保存到JSON文件"""
    print(f"正在保存单词到 {filename}...")
    
    # 可以按首字母分组保存，减少单个文件大小
    word_dict = defaultdict(list)
    for word in word_list:
        first_char = word[0].lower() if word else ''
        word_dict[first_char].append(word)
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(word_dict, f, indent=2, ensure_ascii=False)
    
    print(f"成功保存 {len(word_list)} 个单词到 {filename}")

def main():
    # 获取所有单词
    all_words = get_all_words()
    
    # 保存到JSON文件
    save_words_to_json(all_words)
    
    print("完成！")

if __name__ == "__main__":
    # 首次运行可能需要下载NLTK数据
    try:
        from nltk.corpus import words, wordnet
    except:
        print("需要下载NLTK数据...")
        import nltk
        nltk.download('words')
        nltk.download('wordnet')
    
    main()