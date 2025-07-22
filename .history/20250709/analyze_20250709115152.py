import os
import sys
import pandas as pd
import matplotlib.pyplot as plt
from collections import Counter
from datetime import datetime
import random

# ====== フォント設定（環境に応じて変更） ======
plt.rcParams["font.family"] = "AppleGothic"  # Windows: "MS Gothic" や "Yu Gothic"

# ====== 引数確認 ======
if len(sys.argv) != 4:
    print("使い方: python analyze.py <キーワード> <入力ディレクトリ> <出力ディレクトリ>")
    sys.exit(1)

keyword = sys.argv[1]
input_dir = sys.argv[2]
output_base_dir = sys.argv[3]

# ====== 出力先ディレクトリの生成（日時付き） ======
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
output_dir = os.path.join(output_base_dir, timestamp)
os.makedirs(output_dir, exist_ok=True)

# ====== ユーティリティ関数 ======
def random_color():
    return (random.uniform(0.3, 0.9), random.uniform(0.4, 0.9), random.uniform(0.5, 0.9))

def count_labels(df, column_name="分類ラベル"):
    counter = Counter()
    for val in df[column_name].dropna():
        items = [x.strip() for x in str(val).split(",")]
        unique_items = set(items)
        counter.update(unique_items)
    return counter

def save_bar_chart(counter, title, filepath):
    df = pd.DataFrame(counter.items(), columns=["分類ラベル", "件数"]).sort_values(by="件数", ascending=False)
    colors = [random_color() for _ in range(len(df))]
    plt.figure(figsize=(10, 6))
    plt.bar(df["分類ラベル"], df["件数"], color=colors)
    plt.grid(axis="y", linestyle="--", linewidth=0.5)
    plt.title(title)
    plt.xlabel("分類ラベル")
    plt.ylabel("件数")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(filepath)
    plt.close()

# ====== 対象CSVファイルの取得（ファイル名昇順） ======
matched_files = sorted([
    f for f in os.listdir(input_dir)
    if f.endswith(".csv") and keyword in f
])

if not matched_files:
    print(f"⚠️ 「{keyword}」を含むCSVファイルが見つかりません。")
    sys.exit(0)

print(f"▼ 対象ファイル（{len(matched_files)}件）:")
print("\n".join(matched_files))

# ====== 処理本体 ======
label_file_dict = {}  # {分類ラベル: {ファイル名: 件数}}

for file in matched_files:
    path = os.path.join(input_dir, file)
    try:
        df = pd.read_csv(path, encoding="utf-8-sig")
        if "分類ラベル" not in df.columns:
            print(f"⚠️ 「分類ラベル」列が見つからないためスキップ: {file}")
            continue

        counter = count_labels(df, "分類ラベル")
        base_name = os.path.splitext(file)[0]
        prefix = f"{base_name}"

        # 個別集計CSV・グラフの保存
        df_out = pd.DataFrame(counter.items(), columns=["分類ラベル", "件数"]).sort_values(by="件数", ascending=False)
        df_out.to_csv(os.path.join(output_dir, f"{prefix}_分類ラベル集計.csv"), index=False, encoding="utf-8-sig")
        save_bar_chart(counter, f"{file} の分類ラベル別件数", os.path.join(output_dir, f"{prefix}_分類ラベルグラフ.png"))

        # 積み上げ用のデータに追加
        for label, count in counter.items():
            label_file_dict.setdefault(label, {})[file] = count

        print(f"✔️ {file} → 集計完了")

    except Exception as e:
        print(f"⚠️ エラー（{file}）：{e}")

# ====== 全体積み上げ棒グラフとCSV出力 ======
if label_file_dict:
    stacked_df = pd.DataFrame(label_file_dict).fillna(0).astype(int).T  # 行:ファイル名, 列:分類ラベル
    stacked_df = stacked_df.loc[matched_files]  # ファイル名昇順に整列

    # CSV出力
    matrix_csv = os.path.join(output_dir, f"ファイル別_分類ラベル推移.csv")
    stacked_df.to_csv(matrix_csv, encoding="utf-8-sig")

    # 積み上げ棒グラフ
    ax = stacked_df.plot(
        kind="bar",
        stacked=True,
        figsize=(12, 6),
        colormap="tab20"
    )
    ax.grid(axis="y", linestyle="--", linewidth=0.5)
    plt.title("ファイルごとの分類ラベル件数（積み上げ）")
    plt.xlabel("ファイル名")
    plt.ylabel("件数")
    plt.legend(title="分類ラベル", bbox_to_anchor=(1.02, 1), loc="upper left")
    plt.xticks(rotation=45)
    plt.tight_layout()

    matrix_png = os.path.join(output_dir, f"ファイル別_分類ラベル推移.png")
    plt.savefig(matrix_png)
    plt.close()

    print(f"\n=== 全体グラフ出力完了 ===\n→ {matrix_csv}\n→ {matrix_png}")