import csv
import tiktoken
from datetime import datetime
import os
import pandas as pd

# === 設定 ===
file_path = '/Users/kuramotomana/Test/全課題データ抽出.csv'  # .csv または .xlsx
target_column_names = ["研究概要", "研究目的", "研究方法"]  # 複数列をここに指定
max_tokens_per_list = 8000

# === トークンカウント準備（GPT-4o-mini相当） ===
encoding = tiktoken.get_encoding("cl100k_base")
def count_tokens(text: str) -> int:
    return len(encoding.encode(text))

# === ファイル読み込み＆結合テキストの抽出 ===
combined_values = set()
ext = os.path.splitext(file_path)[1].lower()

if ext == ".csv":
    with open(file_path, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            if all(col in row for col in target_column_names):
                parts = [row[col].strip() for col in target_column_names if row[col].strip()]
                if parts:
                    combined = " ".join(parts)
                    combined_values.add(combined)
elif ext in [".xlsx", ".xls"]:
    df = pd.read_excel(file_path)
    if all(col in df.columns for col in target_column_names):
        for _, row in df[target_column_names].dropna(how="all").iterrows():
            parts = [str(row[col]).strip() for col in target_column_names if pd.notnull(row[col]) and str(row[col]).strip()]
            if parts:
                combined = " ".join(parts)
                combined_values.add(combined)
else:
    raise ValueError("対応していないファイル形式です。CSVかExcelを指定してください。")

# === トークン数でリスト分割 ===
lists = []
current_list = []
current_tokens = 0

for value in sorted(combined_values):
    tokens = count_tokens(value)
    if current_tokens + tokens > max_tokens_per_list:
        lists.append(current_list)
        current_list = [value]
        current_tokens = tokens
    else:
        current_list.append(value)
        current_tokens += tokens
if current_list:
    lists.append(current_list)

# === 出力準備 ===
output_lines = []
output_lines.append(f"✅ ユニークな結合テキスト数: {len(combined_values)}")
output_lines.append(f"✅ 全結合テキストの合計トークン数: {sum(count_tokens(v) for v in combined_values)}")
output_lines.append(f"✅ トークン{max_tokens_per_list}以内に収まるリスト数: {len(lists)}\n")

for i, lst in enumerate(lists):
    token_count = sum(count_tokens(v) for v in lst)
    output_lines.append(f"  ▶ List {i+1}: {len(lst)}項目, 合計トークン数 = {token_count}")

output_lines.append(f"\n🧾 全体のリスト数（分割されたリストの個数）: {len(lists)}")

# === 出力ファイル名作成 ===
base_name = os.path.splitext(os.path.basename(file_path))[0]
timestamp = datetime.now().strftime("%Y%m%d_%H%M")
output_filename = f"/Users/kuramotomana/Test/{timestamp}_{base_name}_token_report.txt"

# === 書き出し ===
with open(output_filename, "w", encoding="utf-8") as f:
    f.write("\n".join(output_lines))

print(f"📝 結果を出力しました: {output_filename}")