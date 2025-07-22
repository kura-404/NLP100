import os
import sys
import pandas as pd
import matplotlib.pyplot as plt
from collections import Counter
from datetime import datetime
import random

# ====== 日本語フォント設定（必要に応じて変更） ======
plt.rcParams["font.family"] = "AppleGothic"  # Windows: 'Yu Gothic', 'MS Gothic'

# ====== 引数確認 ======
if len(sys.argv) != 4:
    print("使い方: python script.py <キーワード> <入力ディレクトリ> <出力ディレクトリ>")
    sys.exit(1)

keyword = sys.argv[1]
input_dir = sys.argv[2]
output_dir = sys.argv[3]
os.makedirs(output_dir, exist_ok=True)
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

# ====== ユーティリティ関数 ======
def random_color():
    return (random.uniform(0.3, 0.9), random.uniform(0.4, 0.9), random.uniform(0.5, 0.9))

def count_categories(df, column_name):
    counter = Counter()
    for val in df[column_name].dropna():
        items = [x.strip() for x in str(val).split(",")]
        unique_items = set(items)
        counter.update(unique_items)
    return counter

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

# ====== 対象ファイル取得（ファイル名の昇順） ======
matched_files = sorted([
    f for f in os.listdir(input_dir)
    if f.endswith(".csv") and keyword in f
])

if not matched_files:
    print(f"⚠️ 「{keyword}」を含むCSVファイルが見つかりません。")
    sys.exit(0)

print(f"▼ 処理対象ファイル（{len(matched_files)}件）:")
print("\n".join(matched_files), "\n")

category_file_dict = {}  # {カテゴリ: {ファイル名: 件数}}

# ====== 各ファイルを処理 ======
for file in matched_files:
    path = os.path.join(input_dir, file)
    try:
        df = pd.read_csv(path)
        if "分類ラベル" not in df.columns:
            print(f"⚠️ 「カテゴリ」列が見つからないためスキップ: {file}")
            continue

        counter = count_categories(df, "分類ラベル")

        # 出力ファイル名プレフィックス
        base_name = os.path.splitext(file)[0]
        output_prefix = f"{timestamp}_{base_name}"

        # CSV保存
        # 修正後
        df_out = pd.DataFrame(counter.items(), columns=["分類ラベル", "件数"])
        # 修正後（任意）
        df_out.to_csv(os.path.join(output_dir, f"{output_prefix}_分類ラベル集計.csv"),

        # グラフ保存
        save_bar_chart(counter, f"{file} のカテゴリ別件数", os.path.join(output_dir, f"{output_prefix}_カテゴリ棒グラフ.png"))

        # 推移用データに追加
        for category, count in counter.items():
            category_file_dict.setdefault(category, {})[file] = count

        print(f"✔️ {file} → 出力完了")

    except Exception as e:
        print(f"⚠️ エラー（{file}）：{e}")

# ====== 全体のカテゴリ×ファイル推移（積み上げ棒グラフ） ======
if category_file_dict:
    cross_df = pd.DataFrame(category_file_dict).fillna(0).astype(int).T  # 行:カテゴリ, 列:ファイル
    cross_df = cross_df[matched_files]  # ファイル名の昇順で整列

    # CSV保存
    csv_path = os.path.join(output_dir, f"{timestamp}_カテゴリ別ファイル推移.csv")
    cross_df.to_csv(csv_path, encoding="utf-8-sig")

    # 積み上げ棒グラフ（区分線＋凡例つき）
    ax = cross_df.plot(
        kind='bar',
        stacked=True,
        figsize=(12, 6),
        colormap='tab20'
    )
    ax.grid(axis='y', linestyle='--', linewidth=0.5)
    plt.title("カテゴリ別件数（ファイルごとの積み上げ推移）")
    plt.xlabel("カテゴリ")
    plt.ylabel("件数")
    plt.legend(title="ファイル名", bbox_to_anchor=(1.02, 1), loc="upper left")
    plt.xticks(rotation=45)
    plt.tight_layout()

    png_path = os.path.join(output_dir, f"{timestamp}_カテゴリ推移グラフ.png")
    plt.savefig(png_path)
    plt.close()

    print(f"\n=== 積み上げグラフ出力完了 ===\n→ {csv_path}, {png_path}")