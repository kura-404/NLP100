import pandas as pd

# CSV読み込み
df = pd.read_csv("/Users/kuramotomana/Test/成果概要.csv")

# '研究年度' を集計し、インデックス（= 年度）で昇順ソート
category_counts = df["研究年度"].value_counts().sort_index()

# 結果表示
print(category_counts)