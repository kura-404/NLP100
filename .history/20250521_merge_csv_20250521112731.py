import glob
import os
from collections import Counter

# ==== 設定 ====
input_dir = "/Users/kuramotomana/Test/term-list"  # CSVファイルが入っているフォルダ
combined_output = "/Users/kuramotomana/Test/term-list/combined_terms.csv"
freq_output = "/Users/kuramotomana/Test/term_frequencies.csv"

# ==== 単語を結合しながらカウント ====
all_files = glob.glob(os.path.join(input_dir, "*.csv"))
all_terms = []

for file in all_files:
    try:
        with open(file, encoding="utf-8") as f:
            line = f.read().strip()
            if line:
                terms = [term.strip() for term in line.split(",") if term.strip()]
                all_terms.extend(terms)
                print(f"✅ 読み込み成功: {file}（{len(terms)} 語）")
    except Exception as e:
        print(f"❌ 読み込み失敗: {file} → {e}")

# ==== 結合出力（カンマ区切り1行） ====
with open(combined_output, "w", encoding="utf-8") as f:
    f.write(",".join(all_terms))

print(f"\n📄 単語リストを結合 → {combined_output}")

# ==== 頻度をカウントしてランキング付きで出力 ====
counter = Counter(all_terms)
with open(freq_output, "w", encoding="utf-8") as f:
    f.write("順位,単語,出現回数\n")
    for rank, (term, count) in enumerate(counter.most_common(), start=1):
        f.write(f"{rank},{term},{count}\n")

print(f"📊 頻度ランキング出力完了 → {freq_output}")
print(f"🔢 単語総数: {len(all_terms)} / ユニーク語数: {len(counter)}")