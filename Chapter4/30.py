# 形態素解析エンジンMeCabのPythonバインディングをインポート
import MeCab 

# MeCabのTaggerオブジェクトを生成
tagger = MeCab.Tagger()

# 対象の日本語テキスト（太宰治『走れメロス』冒頭）
text = """
メロスは激怒した。
必ず、かの邪智暴虐の王を除かなければならぬと決意した。
メロスには政治がわからぬ。
メロスは、村の牧人である。
笛を吹き、羊と遊んで暮して来た。
けれども邪悪に対しては、人一倍に敏感であった。
"""

# MeCabで形態素解析を実行（結果は1単語ごとに改行された文字列）
node = tagger.parse(text)

# 【出力1】MeCabの解析結果
print("MeCabの解析結果")
print(node)

# 動詞の基本形を格納するリスト
verbs = []

# MeCabの解析結果を1行ずつ処理する（1行 = 1形態素）
for line in node.split('\n'):

    # 'EOS'（End Of Sentence）や空行は無視して次の行へ
    if line == 'EOS' or line == '':
        continue

    try:
        # タブで区切られた2つの情報に分ける（表層形と形態素情報）
        surface, feature = line.split('\t')

        # 形態素情報はカンマ区切りの文字列 → リストに変換する
        features = feature.split(',')

        # 品詞（名詞・動詞など）は最初の要素に格納されている
        pos = features[0]

        if pos == '動詞':
            if len(features) > 6 and features[6] != '*':
                base_form = features[6]
                verbs.append(base_form)

    except ValueError:
        # もし正しくタブで分割できなかった行があれば無視（安全策）
        continue

# 【出力2】動詞のリスト（重複除去＆ソート）
print("動詞のリスト")
print(sorted(set(verbs)))