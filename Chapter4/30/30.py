# 形態素解析エンジンMeCabのPythonバインディングをインポート
import MeCab

# 解析対象となる日本語テキスト（複数行の文章）
text = """
メロスは激怒した。
必ず、かの邪智暴虐の王を除かなければならぬと決意した。
メロスには政治がわからぬ。
メロスは、村の牧人である。
笛を吹き、羊と遊んで暮して来た。
けれども邪悪に対しては、人一倍に敏感であった。
"""

# MeCabの解析器オブジェクトを生成（標準設定で初期化）
tagger = MeCab.Tagger()

# 入力テキストをMeCabで形態素解析し、結果を改行区切りの文字列で取得
node = tagger.parse(text)

# 動詞の原形（辞書形）を格納するための空リスト
verbs = []

# MeCabの解析結果を1行ずつ処理
for line in node.split('\n'):

    # 空行や 'EOS'（文の終わり）を無視
    if line == 'EOS' or line == '':
        continue

    try:
        # 各行は「表層形(tab)品詞情報」という形式になっているので分割
        surface, feature = line.split('\t')

        # 品詞情報はカンマ区切りで9個の項目がある
        features = feature.split(',')

        # 最初の要素が「動詞」かつ、原形が'*'でないものだけ対象にする
        if features[0] == '動詞' and features[6] != '*':
            base_form = features[6]  # 原形（例：した → する）を取得
            verbs.append(base_form)  # リストに追加

    except ValueError:
        # splitに失敗した行はスキップ（安全対策）
        continue

# MeCab出力の1行の意味を示す見出し（参考用）
header = "表層形\t品詞,品詞細分類1,品詞細分類2,品詞細分類3,活用形,活用型,原形,読み,発音"

# 【出力1】動詞の原形リストを表示（Pythonのリスト形式）
print("📝 動詞のリスト（Pythonのリスト形式）")
print(verbs)

# 【出力2】MeCabで得られた生の解析結果を出力
print("MeCabの解析結果")
print(header)
print(node)