import pandas as pd

# CSV読み込み
df = pd.read_csv("/Users/kuramotomana/Test/20250519-厚労科研.csv")

# 例：'カテゴリ列名' という列の値を集計
category_counts = df["研究年度"].value_counts()

# 結果表示
print(category_counts)