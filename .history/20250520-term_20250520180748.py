import csv
import json
import time
import os
from datetime import datetime
import pandas as pd
from openai import OpenAI
from tqdm import tqdm
import tiktoken

# ==== 設定 ====
FILE_NAME = "/Users/kuramotomana/Test/20250520fillter.xlsx"
TARGET_COLUMNS = ["研究目的","研究方法","結果と考察",""]
MAX_INPUT_TOKENS = 8000
MAX_OUTPUT_TOKENS = 2000
MAX_TOTAL_TOKENS_PER_BATCH = 1_500_000

# ==== 初期化 ====
client = OpenAI()
encoding = tiktoken.get_encoding("cl100k_base")
os.makedirs("data", exist_ok=True)

# ==== トークンカウント関数 ====
def count_tokens(text):
    return len(encoding.encode(text))

# ==== JSONLファイル保存 ====
def write_jsonl(filename, data):
    with open(filename, 'w', encoding='utf-8') as f:
        for entry in data:
            json.dump(entry, f, ensure_ascii=False)
            f.write('\n')

# ==== バッチ状態確認（リトライあり） ====
def confirm_batch_status(batch_metadata, batch_input_file_id) -> bool:
    batch_status = client.batches.retrieve(batch_metadata.id)
    if batch_status.status == "completed":
        time.sleep(30)
        return True
    elif batch_status.status == "failed":
        print(f"Batch {batch_metadata.id} has failed.")
        retry_count = 0
        while batch_status.status == "failed" and retry_count < 5:
            retry_count += 1
            batch_metadata = client.batches.create(
                input_file_id=batch_input_file_id,
                endpoint="/v1/chat/completions",
                completion_window="24h",
                metadata={"description": f"retry-{retry_count}"}
            )
            batch_status = client.batches.retrieve(batch_metadata.id)
        return batch_status.status == "completed"
    while batch_status.status != "completed":
        time.sleep(60)
        batch_status = client.batches.retrieve(batch_metadata.id)
    return batch_status.status == "completed"

# ==== データ読み込み（Excel）====
df = pd.read_excel(FILE_NAME)
chunks_all = []

for col in TARGET_COLUMNS:
    if col not in df.columns:
        print(f"\u26a0\ufe0f 列 '{col}' が見つかりません。スキップします。")
        continue

    # NaN, 空文字, 空白のみの値を除外し、ユニークに
    values = df[col].dropna().astype(str)
    values = values[values.str.strip() != ""].drop_duplicates()

    # トークン数でチャンク分割（8000以下）
    current_chunk = []
    current_tokens = 0

    for text in values:
        tokens = count_tokens(text)
        if current_tokens + tokens > MAX_INPUT_TOKENS:
            chunks_all.append(("\n".join(current_chunk), col))
            current_chunk = [text]
            current_tokens = tokens
        else:
            current_chunk.append(text)
            current_tokens += tokens

    if current_chunk:
        chunks_all.append(("\n".join(current_chunk), col))

# ==== チャンクをバッチ単位に分割（150万トークン制限）====
requests = []
current_batch = []
current_tokens_sum = 0
batch_counter = 0

def process_batch(batch_id, batch_data):
    jsonl_path = f"data/batch_{batch_id}.jsonl"
    write_jsonl(jsonl_path, batch_data)

    input_file = client.files.create(file=open(jsonl_path, "rb"), purpose="batch")
    metadata = client.batches.create(
        input_file_id=input_file.id,
        endpoint="/v1/chat/completions",
        completion_window="24h",
        metadata={"description": f"batch-{batch_id}"}
    )

    with open("request_input_id.csv", 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        for r in batch_data:
            writer.writerow([jsonl_path, metadata.id, input_file.id])

    success = confirm_batch_status(metadata, input_file.id)
    print(f"{'\u2705' if success else '\u274c'} Batch {batch_id} processed.")
    return

for i, (chunk, col) in enumerate(chunks_all):
    input_tokens = count_tokens(chunk)
    est_total_tokens = input_tokens + MAX_OUTPUT_TOKENS

    if current_tokens_sum + est_total_tokens > MAX_TOTAL_TOKENS_PER_BATCH:
        process_batch(batch_counter, current_batch)
        batch_counter += 1
        current_batch = []
        current_tokens_sum = 0

    request = {
        "custom_id": f"request-{batch_counter}-{i}-{col}",
        "method": "POST",
        "url": "/v1/chat/completions",
        "body": {
            "model": "gpt-4.1-mini",
            "messages": [
                {"role": "system", "content": "次のテキストから用語を抽出してください。出力は抽出した用語のみ、空白区切りで記述してください。"},
                {"role": "user", "content": chunk}
            ],
            "max_tokens": MAX_OUTPUT_TOKENS
        }
    }
    current_batch.append(request)
    current_tokens_sum += est_total_tokens

# ==== 最後のバッチを送信 ====
if current_batch:
    process_batch(batch_counter, current_batch)

# ==== 結果取得と出力 ====
df_request_batch = pd.read_csv("request_input_id.csv", header=None, names=["input_file", "batch_id", "input_file_id"])
batch_ids = df_request_batch['batch_id'].unique().tolist()

terms_list = []
count = 0
for batch_id in tqdm(batch_ids):
    info = client.batches.retrieve(batch_id)
    if info.status == "completed" and info.output_file_id:
        response = client.files.content(info.output_file_id)
        outputs = [json.loads(line) for line in response.text.strip().split('\n')]
        for o in outputs:
            content = o['response']['body']['choices'][0]['message']['content']
            terms = content.strip().split()
            terms_list.extend(terms)
            count += 1

# ==== ファイル出力（重複除去なし） ====
timestamp = datetime.now().strftime("%Y%m%d_%H%M")
base_name = os.path.splitext(os.path.basename(FILE_NAME))[0]
output_filename = f"{timestamp}_{base_name}_terms_only.csv"

with open(output_filename, 'w', encoding='utf-8', newline='') as f:
    f.write(','.join(terms_list))

print(f"\u2705 用語リストを {output_filename} に出力しました")