# JanomeのTokenizerクラスをインポート
from janome.tokenizer import Tokenizer

# 問題文のテキスト
text = """メロスは激怒した。必ず、かの邪智暴虐の王を除かなければならぬと決意した。メロスには政治がわからぬ。メロスは、村の牧人である。笛を吹き
、羊と遊んで暮して来た。けれども邪悪に対しては、人一倍に敏感であった。"""

# Tokenizerのインスタンスを作成
t = Tokenizer()

# 結果を格納するためのリスト
verbs = []

# テキストを形態素解析
# t.tokenize()は、テキストを一つ一つの単語（トークン）に分割する
for token in t.tokenize(text):
    # token.part_of_speechには品詞情報が "動詞,自立,*,*" のように入っている
    # split(',')で分割し、最初の要素（主要な品詞）を取得
    pos = token.part_of_speech.split(',')[0]

    # 品詞が「動詞」の場合
    if pos == '動詞':
        # token.base_formで動詞の基本形（終止形）を取得し、リストに追加
        verbs.append(token.base_form)

# 結果を表示
print(verbs)
