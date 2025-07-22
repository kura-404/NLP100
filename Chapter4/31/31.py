# 形態素解析エンジンMeCabのPythonバインディングをインポート
import MeCab

# 対象となる日本語テキスト（複数行にわたる）
text = """
メロスは激怒した。
必ず、かの邪智暴虐の王を除かなければならぬと決意した。
メロスには政治がわからぬ。
メロスは、村の牧人である。
笛を吹き、羊と遊んで暮して来た。
けれども邪悪に対しては、人一倍に敏感であった。
"""

# MeCabのTaggerオブジェクトを生成（辞書や設定はOS環境に依存）
tagger = MeCab.Tagger()

# MeCabでテキスト全体を形態素解析（品詞情報などを含んだ文字列を取得）
parsed_text = tagger.parse(text)

# 動詞の原型（辞書に載っている形）を保存するための空リストを用意
verbs = []

# MeCabの解析結果は改行区切りなので、1行ずつ処理
for line in parsed_text.split('\n'):

    # 'EOS' は「文の終わり」、空行と一緒にスキップ
    if line == 'EOS' or line == '':
        continue

    try:
        # 各行は「表層形\t品詞情報」の形式なのでタブで分割
        surface, feature = line.split('\t')

        # 品詞情報はカンマ区切り（例：動詞,自立,*,*,五段・ラ行,連用形,する,...）
        features = feature.split(',')

        # 品詞が「動詞」だった場合にのみ処理
        if features[0] == '動詞':
            base_form = features[6]  # 6番目の要素が「基本形」
            verbs.append((surface, base_form))  # 表層形と基本形のペアをリストに追加

    except ValueError:
        # 分割に失敗した場合（不正な行）はスキップ
        continue

# 最後に、結果を整えて表示
print("🔍 動詞とその原型一覧")
for surface, base in verbs:
    print(f"{surface} → {base}")