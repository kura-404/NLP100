import pandas as pd
import matplotlib.pyplot as plt

# CSV読み込み
df = pd.read_csv("/Users/kuramotomana/Test/term-list/term_frequencies.csv")
df = df.sort_values(by="順位")

# 上位1000語に限定（必要に応じて変更）
top_n = 1000
df_top = df[df["順位"] <= top_n]

# 散布図として描画（log-logスケール）
plt.figure(figsize=(10, 6))
plt.scatter(df_top["順位"], df_top["出現回数"], s=10)  # sは点のサイズ

plt.xscale("log")
plt.yscale("log")
plt.title("Term Frequency Ranking (Top 1000, Log-Log Scatter)")
plt.xlabel("Ranking (log scale)")
plt.ylabel("Frequency (log scale)")
plt.grid(True, which='both', linestyle='--', linewidth=0.5)
plt.tight_layout()
plt.show()