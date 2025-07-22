import pandas as pd
import matplotlib.pyplot as plt

# CSV読み込み
df = pd.read_csv("/Users/kuramotomana/Test/term-list/term_frequencies.csv")

# データ型を明示
df["順位"] = df["順位"].astype(int)
df["出現回数"] = df["出現回数"].astype(int)

# 順位でソートしてリセット
df = df.sort_values(by="順位").reset_index(drop=True)

# 上位3000語
top_n = 3000
df_top = df.iloc[:top_n]

# x軸用インデックスを生成（等間隔にする）
x = range(len(df_top))

# 棒グラフ描画（等間隔＋狭いwidth）
plt.figure(figsize=(12, 6))
plt.bar(x, df_top["出現回数"], width=0.8)  # ← 幅を少し細く！

# 縦軸
plt.ylim(0, 4000)

# タイトルやラベル
plt.title("Term Frequency by Ranking (Top 3000)")
plt.xlabel("Ranking (1 to 3000)")
plt.ylabel("Frequency")
plt.grid(True, axis='y', linestyle='--', linewidth=0.5)
plt.tight_layout()
plt.show()