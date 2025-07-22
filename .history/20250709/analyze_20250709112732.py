import os
import sys
import pandas as pd
import matplotlib.pyplot as plt
from collections import Counter
from datetime import datetime
import random

# ====== 日本語フォント設定 ======
plt.rcParams["font.family"] = "AppleGothic"  # Windowsは "Yu Gothic" や "MS Gothic" に変更

# ====== 入力引数チェック ======
if len(sys.argv) != 4:
    print("使い方: python スクリプト.py <キーワード> <入力ディレクトリ> <出力ディレクトリ>")
    sys.exit(1)

keyword = sys.argv[1]
input_dir = sys.argv[2]
output_dir = sys.argv[3]

# 出力ディレクトリ作成
os.makedirs(output_dir, exist_ok=True)

# ====== カラーパレット関数 ======
def random_color():
    return (random.uniform(0.3, 0.9), random.uniform(0.4, 0.9), random.uniform(0.5, 0.9))

# ====== カテゴリ集計関数 ======
def count_categories(df, column_name):
    counter = Counter()
    for val in df[column_name].dropna():
        items = [x.strip() for x in str(val).split(",")]
        unique_items = set(items)
        counter.update(unique_items)
    return counter

# ====== グラフ保存関数 ======
def save_bar_chart(counter, title, filepath):
    count_df = pd.DataFrame(counter.items(), columns=["カテゴリ", "件数"]).sort_values(by="件数", ascending=False)
    colors = [random_color() for _ in range(len(count_df))]

    plt.figure(figsize=(10, 6))
    plt.bar(count_df["カテゴリ"], count_df["件数"], color=colors)
    plt.grid(axis='y', linestyle='--', linewidth=0.5)
    plt.title(title)
    plt.xlabel("カテゴリ")
    plt.ylabel("件数")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(filepath)
    plt.close()

# ====== 処理開始 ======
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
total_counter = Counter()
matched_files = [f for f in os.listdir(input_dir) if f.endswith(".csv") and keyword in f]

if not matched_files:
    print(f"キーワード「{keyword}」を含むCSVファイルが見つかりません。")
    sys.exit(0)

print(f"対象ファイル（{len(matched_files)}件）:")
print("\n".join(matched_files), "\n")

for file in matched_files:
    file_path = os.path.join(input_dir, file)
    try:
        df = pd.read_csv(file_path)
        if "カテゴリ" not in df.columns:
            print(f"⚠️ ファイル「{file}」に列「カテゴリ」が存在しません。スキップします。")
            continue

        counter = count_categories(df, "カテゴリ")
        total_counter.update(counter)

        base_name = os.path.splitext(file)[0]
        output_prefix = f"{timestamp}_{base_name}"

        # CSV保存
        count_df = pd.DataFrame(counter.items(), columns=["カテゴリ", "件数"]).sort_values(by="件数", ascending=False)
        csv_out_path = os.path.join(output_dir, f"{output_prefix}_カテゴリ集計.csv")
        count_df.to_csv(csv_out_path, index=False, encoding="utf-8-sig")

        # グラフ保存
        png_out_path = os.path.join(output_dir, f"{output_prefix}_カテゴリ棒グラフ.png")
        save_bar_chart(counter, f"{file} のカテゴリ別件数", png_out_path)

        print(f"✔️ {file} の集計完了 → {csv_out_path}, {png_out_path}")

    except Exception as e:
        print(f"⚠️ ファイル「{file}」の処理中にエラー：{e}")

# ====== 合計出力 ======
if total_counter:
    total_df = pd.DataFrame(total_counter.items(), columns=["カテゴリ", "件数"]).sort_values(by="件数", ascending=False)
    total_csv = os.path.join(output_dir, f"{timestamp}_全体カテゴリ集計.csv")
    total_png = os.path.join(output_dir, f"{timestamp}_全体カテゴリ棒グラフ.png")
    total_df.to_csv(total_csv, index=False, encoding="utf-8-sig")
    save_bar_chart(total_counter, "全体カテゴリ別件数", total_png)

    print(f"\n=== 全体の集計完了 ===\n→ {total_csv}, {total_png}")