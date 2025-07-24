import MeCab  # MeCabを使うためのインポート

# 対象となる日本語テキスト
text = """
メロスは激怒した。
必ず、かの邪智暴虐の王を除かなければならぬと決意した。
メロスには政治がわからぬ。
メロスは、村の牧人である。
笛を吹き、羊と遊んで暮して来た。
けれども邪悪に対しては、人一倍に敏感であった。
"""

# MeCabのTagger（解析器）を初期化する
tagger = MeCab.Tagger()

# 形態素解析を行い、解析結果を1行ずつ分割
parsed_lines = tagger.parse(text).split('\n')

# 結果を格納するリスト
noun_phrases = []

# 前の単語情報を保存するための変数
prev_noun = None
prev_no = False

# 各行（1単語）を処理
for line in parsed_lines:
    if line == 'EOS' or line == '':
        continue  # EOSや空行はスキップ

    try:
        surface, feature = line.split('\t')  # 表層形と品詞情報に分割
        features = feature.split(',')

        if features[0] == '名詞':  # 名詞の場合
            if prev_no and prev_noun:  # 「名詞 + の + 名詞」のパターンか
                noun_phrases.append(prev_noun + 'の' + surface)
            prev_noun = surface  # 名詞を記憶
            prev_no = False
        elif surface == 'の':  # 「の」が出現したらフラグを立てる
            prev_no = True
        else:
            prev_noun = None
            prev_no = False
    except ValueError:
        continue  # 不正な行はスキップ

# 結果を表示
for phrase in noun_phrases:
    print(phrase)