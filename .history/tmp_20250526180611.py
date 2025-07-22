import pandas as pd

# CSV読み込み
df = pd.read_csv("ファイル名.csv")

# 例：'カテゴリ列名' という列の値を集計
category_counts = df["カテゴリ列名"].value_counts()

# 結果表示
print(category_counts)