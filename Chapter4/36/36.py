import gzip                      # 圧縮ファイルを扱うためのライブラリ
import json                      # JSON形式を読み込むためのライブラリ
import re                        # 正規表現でマークアップを除去
from collections import Counter  # 単語の出現頻度を記録する辞書型の拡張
import MeCab                     # 形態素解析器 MeCab を使う

# MeCabのTaggerを作成（unidic-liteが自動使用される）
tagger = MeCab.Tagger()

# Wikipediaのファイルパス（Google Drive上）
file_path = "/content/drive/MyDrive/jawiki-country.json.gz"

# 単語出現頻度を記録するCounterを初期化
word_counter = Counter()

# gzip形式でファイルを開いて、1記事ずつ読み込む
with gzip.open(file_path, mode='rt', encoding='utf-8') as f:
    for line in f:
        article = json.loads(line)  # JSON文字列をPython辞書に変換
        text = article.get("text", "")  # 本文を取り出す

        # マークアップの簡易除去
        clean_text = re.sub(r'\[\[.*?\]\]', '', text)
        clean_text = re.sub(r"''+", '', clean_text)

        # MeCabで形態素解析
        node = tagger.parseToNode(clean_text)
        while node:
            surface = node.surface             # 表層形（そのままの単語）
            features = node.feature.split(',') # 品詞などの情報を取得
            pos = features[0]                  # 品詞（名詞、助詞など）

            # ノイズとなる語を除外
            if not pos.startswith("補助記号") and not pos.startswith("助詞") and not pos.startswith("助動詞"):
                word_counter[surface] += 1  # 表層形でカウント

            node = node.next  # 次の単語へ

# 出現頻度の高い表層形 上位20語を表示
for word, freq in word_counter.most_common(20):
    print(f"{word}\t{freq}")