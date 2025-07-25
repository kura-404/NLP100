import gzip
import json
import re
import math
from collections import Counter, defaultdict
import MeCab

# MeCabのTaggerを初期化（デフォルト辞書を使用）
tagger = MeCab.Tagger()

# 各記事ごとのTFを格納するリスト
tf_list = []

# 各単語のDF（登場文書数）をカウントする辞書
df_counter = Counter()

# ファイルパス（Google Driveにある前提）
file_path = "/content/drive/MyDrive/jawiki-country.json.gz"

# gzip圧縮されたJSONLファイルを開く
with gzip.open(file_path, mode='rt', encoding='utf-8') as f:
    for line in f:
        article = json.loads(line)  # 各行は1記事のJSON
        text = article.get("text", "")
        title = article.get("title", "")

        # 記事タイトルに「日本」を含まない場合はスキップ
        if "日本" not in title:
            continue

        # [[〜]] や '' のようなマークアップを除去
        clean_text = re.sub(r'\[\[.*?\]\]', '', text)
        clean_text = re.sub(r"''+", '', clean_text)

        # 単語ごとの出現頻度（TF）をカウント
        noun_counter = Counter()
        seen_terms = set()

        node = tagger.parseToNode(clean_text)
        while node:
            surface = node.surface  # 表層形
            features = node.feature.split(',')  # 品詞情報などをカンマで分割
            pos = features[0]  # 品詞の大分類（例：名詞、動詞など）

            # 名詞のみを対象とする
            if pos.startswith("名詞"):
                noun_counter[surface] += 1
                seen_terms.add(surface)
            node = node.next

        tf_list.append(noun_counter)

        for term in seen_terms:
            df_counter[term] += 1

# 文書数
N = len(tf_list)

# 単語ごとのTF-IDFスコアを格納
tfidf_scores = defaultdict(float)

# 各記事ごとのTFを使って、TF-IDFを計算
for tf in tf_list:
    total_terms = sum(tf.values())
    for term, freq in tf.items():
        tf_value = freq / total_terms
        df = df_counter[term]
        idf = math.log((N + 1) / (df + 1)) + 1  # スムージング付きIDF
        tfidf_scores[term] += tf_value * idf

# スコア上位20語を表示
for term, score in sorted(tfidf_scores.items(), key=lambda x: x[1], reverse=True)[:20]:
    tf_sum = sum(tf[term] for tf in tf_list if term in tf)
    idf = math.log((N + 1) / (df_counter[term] + 1)) + 1
    print(f"{term}\tTF: {tf_sum:.4f}\tIDF: {idf:.4f}\tTF-IDF: {score:.4f}")