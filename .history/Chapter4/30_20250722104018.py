import MeCab
import subprocess

# 問題文のテキスト
text = """メロスは激怒した。必ず、かの邪智暴虐の王を除かなければならぬと決意した。メロスには政治がわからぬ。メロスは、村の牧人である。笛を吹き
、羊と遊んで暮して来た。けれども邪悪に対しては、人一倍に敏感であった。"""

# Homebrewでインストールしたmecab-ipadicのパスを自動で取得
# これにより、環境によるパスの違いを吸収できます
cmd = 'echo `mecab-config --dicdir`"/mecab-ipadic"'
dic_path = subprocess.check_output(cmd, shell=True).decode("utf-8").strip()

# MeCabのTagger（形態素解析器）を、辞書のパスを指定して初期化
tagger = MeCab.Tagger(f"-d {dic_path}")

# 結果を格納するためのリスト
verbs = []

# MeCabはparseメソッドで一気に解析する
# 結果は1つの長い文字列で返ってくる
node = tagger.parse(text)

# 結果を改行で分割して、1行（1単語）ずつ処理
for line in node.split('\n'):
    # 'EOS'は文の終わりを示すので無視する
    if line == 'EOS' or line == '':
        continue
    
    # 単語の情報はタブで区切られている（例: メロス\t名詞,固有名詞,...）
    surface, feature = line.split('\t')
    
    # 品詞などの詳細情報はカンマで区切られている
    features = feature.split(',')
    
    # 第1要素が品詞
    pos = features[0]
    
    # 品詞が「動詞」の場合
    if pos == '動詞':
        # 第7要素が基本形。なければ表層形を使う
        base_form = features[6] if features[6] != '*' else surface
        verbs.append(base_form)
        
# 結果を表示
print(verbs)