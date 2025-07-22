import csv
import tiktoken
from datetime import datetime
import os
import pandas as pd

# === 設定 ===
file_path = '/Users/kuramotomana/Test/全課題データ抽出.csv'  # .csv または .xlsx に対応
target_column_name = "研究概要"
max_tokens_per_list = 8000

# === トークンカウント準備（GPT-4o-mini相当） ===
encoding = tiktoken.get_encoding("cl100k_base")
def count_tokens(text: str) -> int:
    return len(encoding.encode(text))

# === ファイル拡張子で分岐してユニーク値を抽出 ===
unique_values = set()
ext = os.path.splitext(file_path)[1].lower()

if ext == ".csv":
    with open(file_path, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            if target_column_name in row:
                value = row[target_column_name].strip()
                if value:
                    unique_values.add(value)
elif ext in [".xlsx", ".xls"]:
    df = pd.read_excel(file_path)
    if target_column_name in df.columns:
        for value in df[target_column_name].dropna().unique():
            value = str(value).strip()
            if value:
                unique_values.add(value)
else:
    raise ValueError("対応していないファイル形式です。CSVかExcelを指定してください。")

# === トークン数でリスト分割 ===
lists = []
current_list = []
current_tokens = 0

for value in sorted(unique_values):
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
output_lines.append(f"✅ ユニークな値の数: {len(unique_values)}")
output_lines.append(f"✅ 全ユニークデータの合計トークン数: {sum(count_tokens(v) for v in unique_values)}")
output_lines.append(f"✅ トークン{max_tokens_per_list}以内に収まるリスト数: {len(lists)}\n")

for i, lst in enumerate(lists):
    token_count = sum(count_tokens(v) for v in lst)
    output_lines.append(f"  ▶ List {i+1}: {len(lst)}項目, 合計トークン数 = {token_count}")

output_lines.append(f"\n🧾 全体のリスト数（分割されたリストの個数）: {len(lists)}")

# === ファイル名生成（現在時刻＋元ファイル名）===
base_name = os.path.splitext(os.path.basename(file_path))[0]
timestamp = datetime.now().strftime("%Y%m%d_%H%M")
output_filename = f"/Users/kuramotomana/Test/{timestamp}_{base_name}_token_report.txt"

# === テキストファイルに書き込み ===
with open(output_filename, "w", encoding="utf-8") as f:
    f.write("\n".join(output_lines))

print(f"📝 結果を出力しました: {output_filename}")

with open(output_filename, "w", encoding="utf-8") as f:
    f.write("\n".join(output_lines))

print(f"📝 結果を出力しました: {output_filename}")