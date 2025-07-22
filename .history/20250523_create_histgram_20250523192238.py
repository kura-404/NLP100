import pandas as pd
import matplotlib.pyplot as plt

# 読み込み
df = pd.read_csv("/Users/kuramotomana/Test/term-list/term_frequencies.csv")

# 順位でソート（念のため）
df = df.sort_values(by="順位")

# 上位1000語だけに絞る
top_n = 1000
df_top = df[df["順位"] <= top_n]

# プロット
plt.figure(figsize=(10, 6))
plt.plot(df_top["順位"], df_top["出現回数"], marker='o', linestyle='-')
plt.xscale("log")  # 横軸：対数
plt.yscale("log")  # 縦軸：対数
plt.title("Term Frequency Ranking (Top 1000, Log-Log Scale)")
plt.xlabel("Ranking (log scale)")
plt.ylabel("Frequency (log scale)")
plt.grid(True, which='both', linestyle='--', linewidth=0.5)
plt.tight_layout()
plt.show()