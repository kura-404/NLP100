import ginza

# ginza 経由で spaCy の日本語モデルをロード（内部的に ELECTRA 使用）
nlp = ginza.load()

text = """
メロスは激怒した。
必ず、かの邪智暴虐の王を除かなければならぬと決意した。
メロスには政治がわからぬ。
メロスは、村の牧人である。
笛を吹き、羊と遊んで暮して来た。
けれども邪悪に対しては、人一倍に敏感であった。
"""

doc = nlp(text)

# 動詞の基本形を抽出（token.pos_ == "VERB"）
verbs = [token.lemma_ for token in doc if token.pos_ == "VERB"]

print("抽出された動詞（基本形）:")
print(sorted(set(verbs)))
