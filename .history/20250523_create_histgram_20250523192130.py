import pandas as pd
import matplotlib.pyplot as plt

# CSVの読み込み
df = pd.read_csv("/Users/kuramotomana/Test/term-list/term_frequencies.csv")

# 順位順にソート（念のため）
df = df.sort_values(by="順位")

# 出現回数をプロット
plt.figure(figsize=(12, 6))
plt.plot(df["順位"], df["出現回数"], marker='o', linestyle='-')

plt.title("Term Frequency Ranking (Long Tail)")
plt.xlabel("Ranking")
plt.ylabel("Frequency")
plt.grid(True)
plt.tight_layout()
plt.show()