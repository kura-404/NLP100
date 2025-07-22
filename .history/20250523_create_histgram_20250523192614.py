import pandas as pd
import matplotlib.pyplot as plt

# CSV読み込み
df = pd.read_csv("/Users/kuramotomana/Test/term-list/term_frequencies.csv")

# 順位でソート
df = df.sort_values(by="順位")

# 上位100語に限定（多すぎると棒が細くなりすぎるため）
top_n = 2000
df_top = df[df["順位"] <= top_n]

# 棒グラフ描画（ラベルは順位の数値）
plt.figure(figsize=(12, 6))
plt.bar(df_top["順位"], df_top["出現回数"], width=1.0)

plt.title("Term Frequency by Ranking (Top 100)")
plt.xlabel("Ranking")
plt.ylabel("Frequency")
plt.grid(True, axis='y', linestyle='--', linewidth=0.5)
plt.tight_layout()
plt.show()