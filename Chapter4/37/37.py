import gzip  # gzip形式のファイルを読み込むためのライブラリ
import json  # JSONデータを扱うためのライブラリ
from collections import Counter  # 単語の頻度を数えるために使う辞書型
import MeCab  # 日本語の文章を形態素に分解するライブラリ

tagger = MeCab.Tagger()  # MeCabのTaggerオブジェクトを生成（辞書はunidic-liteを前提）

file_path = "/path/to/jawiki-country.json.gz"  # 圧縮されたWikipediaデータのファイルパス
noun_counter = Counter()  # 名詞の頻度を記録するCounterオブジェクトを作成

# 圧縮されたファイルをテキストモード（文字列）で開く
with gzip.open(file_path, mode='rt', encoding='utf-8') as f:
    for line in f:  # ファイルを1行ずつ読み込む（1行＝1記事）
        article = json.loads(line)  # 1行のJSON文字列を辞書に変換
        text = article.get("text", "")  # 辞書から本文（text）を取り出す

        node = tagger.parseToNode(text)  # MeCabで形態素解析し、最初のノードを取得
        while node:  # ノードが存在する間、ループを続ける
            features = node.feature.split(',')  # ノードの品詞情報をカンマで分割
            pos = features[0]  # 品詞の大分類（名詞・動詞など）を取り出す

            if pos == "名詞":  # 名詞の場合だけカウントする
                surface = node.surface  # 表層形（そのままの文字列）を取得
                noun_counter[surface] += 1  # Counterで頻度を1加算

            node = node.next  # 次のノードへ進む

# 出現頻度の高い名詞20語を表示
for word, freq in noun_counter.most_common(20):
    print(f"{word}\t{freq}")