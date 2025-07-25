# spaCyライブラリをインポートする（自然言語処理の本体）
import spacy

# GiNZAの日本語モデルを読み込む（形態素解析＋構文解析を行う）
nlp = spacy.load("ja_ginza")

# 解析対象の文章を複数行で定義する
text = """
メロスは激怒した。
必ず、かの邪智暴虐の王を除かなければならぬと決意した。
メロスには政治がわからぬ。
メロスは、村の牧人である。
笛を吹き、羊と遊んで暮して来た。
けれども邪悪に対しては、人一倍に敏感であった。
"""

# 文章をGiNZAで解析し、文・単語単位の情報を持つDocオブジェクトに変換
doc = nlp(text)

# 抽出した述語（動詞や名詞述語）を格納するためのリストを初期化
predicates = []

# 文単位で処理する
for sent in doc.sents:
    # 各文に含まれる単語を1語ずつ処理
    for token in sent:
        # 「メロス」が主語（nsubj）として使われている単語を探す
        if token.text == "メロス" and token.dep_ == "nsubj":
            # 「メロス」がかかっている語（述語候補）を取得
            head = token.head

            # 述語が動詞や助動詞である場合は、その語を記録
            if head.pos_ in ("VERB", "AUX"):
                predicates.append(head.text)

            # 述語が名詞で、「〜である」など名詞述語になっている場合
            elif head.pos_ == "NOUN":
                # 補助述語（copula）と、その後のfixed要素（例：ある）を探す
                cop_found = None
                fixed_found = None

                # head（名詞）に付属する単語を調べる
                for child in head.children:
                    # cop（助動詞：「で」など）を探す
                    if child.dep_ == "cop":
                        cop_found = child
                        # copにくっついている「ある」などの固定表現（fixed）を探す
                        for grandchild in child.children:
                            if grandchild.dep_ == "fixed":
                                fixed_found = grandchild

                # 「名詞 + で + ある」の3語構成がある場合
                if cop_found and fixed_found:
                    predicates.append(f"{head.text}{cop_found.text}{fixed_found.text}")
                # 「名詞 + で」までしかない場合
                elif cop_found:
                    predicates.append(f"{head.text}{cop_found.text}")
                # 名詞単独しかない場合
                else:
                    predicates.append(head.text)

# 重複を除いた述語リストをソートして表示する
print(sorted(set(predicates)))