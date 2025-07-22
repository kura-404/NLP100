import pandas as pd
from openai import OpenAI
from dotenv import load_dotenv
import os
import csv
from datetime import datetime

# タイムスタンプ付きファイル名を定義
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
output_file = f"baseline_rewritten_output_{timestamp}.csv"

# .envからAPIキー読み込み
load_dotenv()

# OpenAIクライアント初期化
client = OpenAI()

# データ読み込み
df = pd.read_excel("テスト用データ.xlsx")

# 除外する列を定義
excluded_cols = ["研究概要", "成果概要（日本語）", "各IDの最新年度", "フラグ", "ランダムフラグ"]

# 「研究課題名」を課題IDの直後に、それ以外の列をそのまま出力
extra_columns_ordered = ["研究課題名"] + [
    col for col in df.columns if col not in excluded_cols + ["研究課題名"]
]

# ヘッダー列定義
header_columns = [
    "課題管理番号", "課題ID", "研究課題名",
    "書き換え前：研究概要", "書き換え後：研究概要",
    "書き換え前：成果概要", "書き換え後：成果概要"
] + extra_columns_ordered[1:]  # 「研究課題名」はすでに含めている

# ヘッダーを書き込む
with open(output_file, mode="w", encoding="utf-8-sig", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=header_columns)
    writer.writeheader()

# ランダムに3件抽出（必要に応じて変更可能）
sampled = df

# 各行を処理
for _, row in sampled.iterrows():
    kmn = row.get("課題管理番号", "")
    kid = row.get("課題ID", "")
    before_rg = row.get("研究概要", "")
    before_sg = row.get("成果概要（日本語）", "")

    # --- 研究概要ターン ---
    try:
        completion_rg = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[
                {"role": "system", "content": "以下の研究概要を伝わるように改善してください。前置きのコメントや説明は不要です。書き換えた文章だけを出力してください。"},
                {"role": "user", "content": before_rg}
            ],
            temperature=0.5
        )
        after_rg = completion_rg.choices[0].message.content.strip()
    except Exception as e:
        after_rg = f"エラー発生: {e}"

    # --- 成果概要ターン ---
    try:
        completion_sg = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[
                {"role": "system", "content": "以下の成果概要を伝わるように改善してください。前置きのコメントや説明は不要です。書き換えた文章だけを出力してください。"},
                {"role": "user", "content": before_sg}
            ],
            temperature=0.5
        )
        after_sg = completion_sg.choices[0].message.content.strip()
    except Exception as e:
        after_sg = f"エラー発生: {e}"

    # 書き出し用データを構成
    row_data = {
        "課題管理番号": kmn,
        "課題ID": kid,
        "研究課題名": row.get("研究課題名", ""),
        "書き換え前：研究概要": before_rg,
        "書き換え後：研究概要": after_rg,
        "書き換え前：成果概要": before_sg,
        "書き換え後：成果概要": after_sg
    }

    # 他の列も後ろに追記
    for col in extra_columns_ordered[1:]:  # 研究課題名はすでに記述済み
        row_data[col] = row.get(col, "")

    # 書き込み（追記）
    with open(output_file, mode="a", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=header_columns)
        writer.writerow(row_data)