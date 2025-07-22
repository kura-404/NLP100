import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv("/Users/kuramotomana/Test/term-list/term_frequencies.csv")
df = df.sort_values(by="順位")
top_n = 3000
df_top = df[df["順位"] <= top_n]

plt.figure(figsize=(12, 6))
plt.bar(df_top["順位"], df_top["出現回数"], width=1.0)

# 方法①：縦軸の表示範囲を制限（例：500まで）
plt.ylim(0, 500)

# タイトルや軸
plt.title("Term Frequency by Ranking (Top 3000, Truncated Y)")
plt.xlabel("Ranking")
plt.ylabel("Frequency")
plt.grid(True, axis='y', linestyle='--', linewidth=0.5)
plt.tight_layout()
plt.show()