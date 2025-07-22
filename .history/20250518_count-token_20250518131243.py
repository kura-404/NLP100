#csvファイルを読み込んで8000トークンごとに1リストにしてリストが幾つできるかを確認するコード
import csv
import tiktoken

csv_file_path="/Users/kuramotomana/Test/成果概要.csv"
target_column_name="成果概要（日本語）"
max_tokens_per_list=8000

# === トークンカウント準備（cl100k_base = GPT-4o-mini相当） ===
encoding = tiktoken.get_encoding("cl100k_base")

def count_tokens(text: str) -> int:
    return len(encoding.encode(text))

# === ユニークな値を抽出 ===
unique_values = set()
with open(csv_file_path, newline='', encoding='utf-8') as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
        if target_column_name in row:
            value = row[target_column_name].strip()
            if value:
                unique_values.add(value)

# === トークン数で分割 ===
lists = []
current_list = []
current_tokens = 0

for value in sorted(unique_values):  # 任意にソート
    tokens = count_tokens(value)
    if current_tokens + tokens > max_tokens_per_list:
        lists.append(current_list)
        current_list = [value]
        current_tokens = tokens
    else:
        current_list.append(value)
        current_tokens += tokens

# 最後のリストを追加
if current_list:
    lists.append(current_list)

# === 出力 ===
print(f"✅ ユニークな値の数: {len(unique_values)}")
print(f"✅ 全ユニークデータの合計トークン数: {sum(count_tokens(v) for v in unique_values)}")
print(f"✅ トークン8000以内に収まるリスト数: {len(lists)}")

# 各リストの詳細
for i, lst in enumerate(lists):
    token_count = sum(count_tokens(v) for v in lst)
    print(f"  ▶ List {i+1}: {len(lst)}項目, 合計トークン数 = {token_count}")

# リストの数を強調して再表示
print(f"\n🧾 全体のリスト数（分割されたリストの個数）: {len(lists)}")