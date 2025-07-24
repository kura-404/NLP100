# MeCabをインポート（形態素解析のためのライブラリ）
import MeCab

# 対象の日本語テキスト（複数行の文章）
text = """
メロスは激怒した。
必ず、かの邪智暴虐の王を除かなければならぬと決意した。
メロスには政治がわからぬ。
メロスは、村の牧人である。
笛を吹き、羊と遊んで暮して来た。
けれども邪悪に対しては、人一倍に敏感であった。
"""

# MeCabのTaggerオブジェクトを生成
tagger = MeCab.Tagger()

# 形態素解析を実行し、結果を取得（1語ずつ改行されたテキスト形式）
parsed = tagger.parse(text)

# 動詞の原形を格納するリストを初期化
verb_base_forms = []

# 解析結果を1行ずつ処理
for line in parsed.split('\n'):
    if line == 'EOS' or line == '':
        continue  # 終端記号や空行はスキップ
    try:
        surface, feature = line.split('\t')  # 表層形と品詞情報に分割
        features = feature.split(',')        # 品詞情報をカンマで分割
        if features[0] == '動詞':             # 品詞が「動詞」のものだけを対象
            base_form = features[6]          # 原形（辞書形）は6番目の要素
            verb_base_forms.append((surface, base_form))  # 表層形と原形のペアを保存
    except ValueError:
        continue  # フォーマットエラー時はスキップ

# 結果を出力
print("🔍 動詞とその原形一覧")
for surface, base in verb_base_forms:
    print(f"{surface} → {base}")