import pandas as pd
from fugashi import Tagger
from jreadability import compute_readability
import argparse
from datetime import datetime

# --- 引数の処理 ---
parser = argparse.ArgumentParser(description="Readability score calculator")
parser.add_argument("keyword", type=str, help="出力ファイル名に含めるキーワード")
parser.add_argument("--input", type=str, default="input.csv", help="入力CSVファイル名（デフォルト: input.csv）")
args = parser.parse_args()

# --- 日時とファイル名の組み合わせ ---
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
output_csv = f"{timestamp}_{args.keyword}_calcurate.csv"

# --- 可読性を計算する列（日本語カラム名対応） ---
text_columns = [
    "書き換え前：研究概要",
    "書き換え後：研究概要",
    "書き換え前：成果概要",
    "書き換え後：成果概要"
]

# --- CSV読み込み ---
df = pd.read_csv(args.input)

# --- Tagger初期化（高速化） ---
tagger = Tagger()

# --- 可読性スコア計算関数 ---
def calc_score(text):
    if pd.isna(text) or not isinstance(text, str) or text.strip() == "":
        return None
    try:
        return compute_readability(text, tagger)
    except Exception as e:
        print(f"Error in: {text[:30]}... → {e}")
        return None

# --- スコア列の追加 ---
for col in text_columns:
    # スコア列名の自動命名（例：score_研究概要_before）
    suffix = (
        "before" if "書き換え前" in col else
        "after" if "書き換え後" in col else
        "unknown"
    )
    if "研究概要" in col:
        base = "研究概要"
    elif "成果概要" in col:
        base = "成果概要"
    else:
        base = "unknown"

    score_col = f"score_{base}_{suffix}"
    df[score_col] = df[col].apply(calc_score)

# --- 出力列の順序調整（元列＋対応スコア列を隣接配置） ---
output_columns = []
for col in df.columns:
    output_columns.append(col)
    if col in text_columns:
        suffix = (
            "before" if "書き換え前" in col else
            "after" if "書き換え後" in col else
            "unknown"
        )
        if "研究概要" in col:
            base = "研究概要"
        elif "成果概要" in col:
            base = "成果概要"
        else:
            base = "unknown"
        score_col = f"score_{base}_{suffix}"
        output_columns.append(score_col)

# --- BOM付きUTF-8でCSV保存（Excel対策） ---
df.to_csv(output_csv, index=False, columns=output_columns, encoding="utf-8-sig")

print(f"完了しました。出力ファイル: {output_csv}")