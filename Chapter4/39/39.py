# 必要なライブラリをインポート
import gzip                    # .gz形式の圧縮ファイルを扱うためのライブラリ
import json                   # JSON形式のデータを扱うためのライブラリ
import re                     # 正規表現を使ってテキストを整形
from collections import Counter  # 単語の出現回数を数えるためのカウンター
import matplotlib.pyplot as plt  # グラフ描画用ライブラリ
import matplotlib.font_manager as fm  # フォント設定用ライブラリ
import MeCab                  # 日本語形態素解析器

# Colabに標準で入っているIPAexゴシックのフォントパスを指定
font_path = "/usr/share/fonts/opentype/ipaexfont-gothic/ipaexg.ttf"
fp = fm.FontProperties(fname=font_path)

# MeCabのTaggerを作成（形態素解析器の準備）
tagger = MeCab.Tagger()

# 単語の出現頻度を記録するカウンターを初期化
word_counter = Counter()

# Wikipediaの圧縮JSONファイルのパス（事前にGoogle Driveにアップロードしておく）
file_path = "/content/drive/MyDrive/jawiki-country.json.gz"

# 圧縮ファイルを開いて1行ずつ読み込み
with gzip.open(file_path, mode='rt', encoding='utf-8') as f:
    for line in f:
        # 1行ずつJSON形式で辞書に変換
        article = json.loads(line)
        text = article.get("text", "")  # "text"キーの値を取得（本文）

        # Wikipedia特有のマークアップ（リンクや強調）を除去
        clean_text = re.sub(r'\[\[.*?\]\]', '', text)
        clean_text = re.sub(r"''+", '', clean_text)

        # 形態素解析の準備（ノード単位で処理）
        node = tagger.parseToNode(clean_text)
        while node:
            surface = node.surface               # 表層形（見た目の単語）
            features = node.feature.split(',')   # 品詞などの情報をカンマ区切りで取得
            pos = features[0]                    # 品詞の主分類を取得（例：名詞・動詞）
            if pos.startswith("名詞"):           # 名詞だけをカウント対象にする
                word_counter[surface] += 1       # 単語の出現回数を1つ増やす
            node = node.next                     # 次のノードへ

# 頻度の高い順に単語を並べる
sorted_counts = word_counter.most_common()

# 単語の順位（1位から順番）と、その頻度をそれぞれリスト化
ranks = list(range(1, len(sorted_counts) + 1))
frequencies = [freq for _, freq in sorted_counts]

# グラフの描画設定
plt.figure(figsize=(10, 6))  # グラフのサイズを指定
plt.plot(ranks, frequencies)  # 順位 vs 出現頻度のグラフを描く
plt.xscale("log")             # 横軸を対数スケールにする
plt.yscale("log")             # 縦軸も対数スケールにする
plt.xlabel("出現頻度順位（対数）", fontproperties=fp)  # 横軸ラベル（日本語）
plt.ylabel("出現頻度（対数）", fontproperties=fp)      # 縦軸ラベル（日本語）
plt.title("Zipfの法則に基づく単語頻度分布（日本語 Wikipedia）", fontproperties=fp)  # タイトル
plt.grid(True)               # グリッド線を表示
plt.tight_layout()           # レイアウトを自動調整
plt.show()                   # グラフを表示