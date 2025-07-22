import pandas as pd
import matplotlib.pyplot as plt

# CSV読み込み
df = pd.read_csv("/Users/kuramotomana/Test/term-list/term_frequencies.csv")

# 数値に変換（明示的に）
df["順位"] = df["順位"].astype(int)
df["出現回数"] = df["出現回数"].astype(int)

# 順位順にソート
df = df.sort_values(by="順位").reset_index(drop=True)

# 上位1000件を抽出
top_n = 1500
df_top = df.iloc[:top_n]

# x軸：0〜999 の等間隔インデックス
x = range(top_n)

# 描画（棒幅や解像度を自動調整）
plt.figure(figsize=(14, 6))
plt.bar(x, df_top["出現回数"], width=1.0)

# 軸とラベル
plt.title("Term Frequency by Ranking (Top 1000, Accurate Height)")
plt.xlabel("Ranking")
plt.ylabel("Frequency")
plt.grid(True, axis='y', linestyle='--', linewidth=0.5)

# 自動調整（はみ出し回避）
plt.tight_layout()
plt.show()