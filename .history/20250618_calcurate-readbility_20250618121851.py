#python readability_batch.py mykeyword --input myfile.csv
import pandas as pd
from fugashi import Tagger
from jreadability import compute_readability
import argparse
from datetime import datetime

# === コマンドライン引数の処理 ===
parser = argparse.ArgumentParser(description="Readability score calculator")
parser.add_argument("keyword", type=str, help="出力ファイル名に含めるキーワード")
parser.add_argument("--input", type=str, default="input.csv", help="入力CSVファイル名（デフォルト: input.csv）")
args = parser.parse_args()

# === 日時付きの出力ファイル名を作成 ===
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
output_csv = f"{timestamp}_{args.keyword}_calcurate.csv"

# === スコアを計算したい列を指定 ===
text_columns = ["書き換え前研究概要”, "書き換え後：研究概要", "書き換え前：成果概要", "書き換え後：成果概要"]

# === CSV読み込み ===
df = pd.read_csv(args.input)

# === Tagger初期化（1回だけ） ===
tagger = Tagger()

# === 可読性スコアの関数 ===
def calc_score(text):
    if pd.isna(text) or not isinstance(text, str) or text.strip() == "":
        return None
    try:
        return compute_readability(text, tagger)
    except Exception as e:
        print(f"Error in: {text[:30]}... → {e}")
        return None

# === 各テキスト列にスコア列を追加 ===
for col in text_columns:
    score_col = f"score_{col.split('_')[-1]}"
    df[score_col] = df[col].apply(calc_score)

# === 出力列の順序を整える（元の列＋スコア列） ===
output_columns = []
for col in df.columns:
    output_columns.append(col)
    if col in text_columns:
        score_col = f"score_{col.split('_')[-1]}"
        output_columns.append(score_col)

# === 出力保存 ===
df.to_csv(output_csv, index=False, columns=output_columns)
print(f"完了しました。'{output_csv}' に保存しました。")