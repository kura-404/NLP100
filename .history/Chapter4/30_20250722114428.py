import MeCab

# 問題文のテキスト
text = """
メロスは激怒した。
必ず、かの邪智暴虐の王を除かなければならぬと決意した。
メロスには政治がわからぬ。
メロスは、村の牧人である。
笛を吹き、羊と遊んで暮して来た。
けれども邪悪に対しては、人一倍に敏感であった。
"""

# 【★★これが今回のポイント★★】
# 引数を何も与えずにMeCabを初期化します。
# これにより、正常に存在することを確認した設定ファイルが自動的に使われます。
tagger=MeCab.Tagger()

# 結果を格納するためのリスト
verbs=[]

# MeCabはparseメソッドで一気に解析する
node = tagger.parse(text)

# 結果を改行で分割して、1行（1単語）ずつ処理
for line in node.split('\n'):
    if line == 'EOS' or line == '':
        continue
    surface, feature = line.split('\t')
    features = feature.split(',')
    
    pos = features[0]
    
    if pos == '動詞':
        base_form = features[6] if features[6] != '*' else surface
        verbs.append(base_form)
        
# 結果を表示
print(verbs)