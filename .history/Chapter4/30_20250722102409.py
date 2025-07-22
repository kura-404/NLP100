import spacy

# GiNZA ELECTRA モデルをロード
nlp = spacy.load("ja_ginza_electra")

# 文章テキスト
text = """
メロスは激怒した。
必ず、かの邪智暴虐の王を除かなければならぬと決意した。
メロスには政治がわからぬ。
メロスは、村の牧人である。
笛を吹き、羊と遊んで暮して来た。
けれども邪悪に対しては、人一倍に敏感であった。
"""

# 解析
doc = nlp(text)

# 動詞の基本形を抽出
verbs = [token.lemma_ for token in doc if token.pos_ == "VERB"]

# 結果表示（重複を除いてソート）
print("抽出された動詞（基本形）:")
print(sorted(set(verbs)))