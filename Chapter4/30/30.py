# 形態素解析エンジンMeCabのPythonバインディングをインポート
import MeCab

# MeCabのTaggerオブジェクトを生成（辞書や動作設定はOSに依存して自動選択される）
tagger = MeCab.Tagger()

# MeCabでテキスト全体を形態素解析し、解析結果を改行区切りの文字列として取得
node = tagger.parse(text)

# 動詞の基本形（辞書に載っている元の形）を保存するためのリストを作成
verbs = []

# MeCabの出力は1語ごとに1行なので、改行で分割して1行ずつ処理
for line in node.split('\n'):

    # 'EOS' は MeCab における「文の終わり」のマーク。空行とともにスキップする
    if line == 'EOS' or line == '':
        continue

    try:
        # 各行は「表層形（表示される形） + タブ + 品詞情報」の形式なので、分ける
        surface, feature = line.split('\t')

        # 品詞情報（「名詞,一般,*,*,*,*,〜」のようなカンマ区切りの情報）を分割
        features = feature.split(',')

        # 品詞情報の0番目（features[0]）が「動詞」だったら処理を進める
        if features[0] == '動詞':

            # features[6] は「基本形」（例：した → する）を表す
            # "*" の場合は値がないのでスキップ
            if features[6] != '*':
                base_form = features[6]  # 基本形を取り出す
                verbs.append(base_form)  # 動詞リストに追加

    except ValueError:
        # 行にタブが含まれていないなど、splitに失敗した場合はスキップ
        continue

# 【出力1】MeCabの解析結果をそのまま表示（省略なし）
print("🔍 MeCabの解析結果（全文）")
print(node)

# 【出力2】Pythonのリスト形式で動詞の基本形をすべて表示（重複は残す）
print("📝 動詞のリスト（Pythonのリスト形式）")
print(verbs)