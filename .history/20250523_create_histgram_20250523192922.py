import pandas as pd
import matplotlib.pyplot as plt

# CSV読み込み
df = pd.read_csv("/Users/kuramotomana/Test/term-list/term_frequencies.csv")

# 順位でソート
df = df.sort_values(by="順位")

# 上位3000語に限定
top_n = 3000
df_top = df[df["順位"] <= top_n]

# 棒グラフ描画
plt.figure(figsize=(12, 6))
plt.bar(df_top["順位"], df_top["出現回数"], width=1.0)

# 縦軸の表示範囲を制限（0〜500）
plt.ylim(0, 500)

# ラベルとタイトルなど
plt.title("Term Frequency by Ranking (Top 3000, Y limit 500)")
plt.xlabel("Ranking")
plt.ylabel("Frequency")
plt.grid(True, axis='y', linestyle='--', linewidth=0.5)
plt.tight_layout()
plt.show()