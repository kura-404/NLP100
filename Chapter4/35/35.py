# spaCyから構文可視化ツールdisplacyをインポート
from spacy import displacy

# Google ColabなどでHTMLを表示するために必要なdisplay関数をインポート
from IPython.display import display, HTML

# 日本語処理のためにspaCyをインポート
import spacy

# GiNZAモデルを読み込む（インストール済みである必要があります）
nlp = spacy.load("ja_ginza")

# 対象の日本語の文を定義
text = "メロスは激怒した。"

# GiNZAで文を解析してDocオブジェクトに変換
doc = nlp(text)

# displacyで依存構造（係り受け木）をHTMLとしてレンダリング（compact表示）
html = displacy.render(doc, style="dep", options={"compact": True})

# Colab上でHTMLを表示
display(HTML(html))