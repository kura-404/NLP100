import pandas as pd
import matplotlib.pyplot as plt

# CSV読み込み
df = pd.read_csv("/Users/kuramotomana/Test/term-list/term_frequencies.csv")

# 順位でソート（念のため）
df = df.sort_values(by="順位")

# 上位30語に限定
top_n = 30
df_top = df[df["順位"] <= top_n]

# 棒グラフ描画
plt.figure(figsize=(12, 6))
plt.bar(df_top["単語"], df_top["出現回数"])

plt.xticks(rotation=60, ha='right')  # 横軸ラベルの読みやすさ対策
plt.title("Top 30 Terms by Frequency")
plt.xlabel("Term")
plt.ylabel("Frequency")
plt.tight_layout()
plt.show()