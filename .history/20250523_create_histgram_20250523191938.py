import pandas as pd
import matplotlib.pyplot as plt

# CSVの読み込み
df = pd.read_csv("/Users/kuramotomana/Test/term-list/term_frequencies.csv)

# 特定の列のヒストグラム（例：'age'列）
plt.hist(df["age"].dropna(), bins=20, edgecolor='black')  # dropna()で欠損値を除く
plt.title("Histogram of Age")
plt.xlabel("Age")
plt.ylabel("Frequency")
plt.grid(True)
plt.show()