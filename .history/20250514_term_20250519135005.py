#1リクエスト10000トークン/150万トークンで１バッチ
import csv
import json
import time
import os
from datetime import datetime

import pandas as pd
from openai import OpenAI
from tqdm import tqdm
import tiktoken

#%% OpenAIクライアント初期化
client = OpenAI()

#%% トークンカウント準備（cl100k_base = gpt-4.1-mini相当）
encoding = tiktoken.get_encoding("cl100k_base")

def count_tokens(text):
    return len(encoding.encode(text))

#%% バッチ状態確認関数（リトライあり）
def confirm_batch_status(batch_metadata, batch_input_file_id) -> bool:
    batch_status = client.batches.retrieve(batch_metadata.id)

    if batch_status.status == "completed":
        time.sleep(30)
        return True
    elif batch_status.status == "failed":
        print(f"Batch {batch_metadata.id} has failed.")
        retry_count = 0
        max_retries = 5
        while batch_status.status == "failed" and retry_count < max_retries:
            retry_count += 1
            batch_metadata = client.batches.create(
                input_file_id=batch_input_file_id,
                endpoint="/v1/chat/completions",
                completion_window="24h",
                metadata={"description": "count word retry"}
            )
            batch_status = client.batches.retrieve(batch_metadata.id)
        return batch_status.status == "completed"

    while batch_status.status != "completed":
        time.sleep(60)
        batch_status = client.batches.retrieve(batch_metadata.id)
    return batch_status.status == "completed"

#%% JSONLファイルの書き込み関数
def write_jsonl(filename, data):
    with open(filename, 'w', encoding='utf-8') as f:
        for entry in data:
            json.dump(entry, f, ensure_ascii=False)
            f.write('\n')

#%% ファイル読み込みとチャンク分割
FILE_NAME = "/Users/kuramotomana/Test/成果概要.csv"
df = pd.read_csv(FILE_NAME, encoding='utf-8-sig')

# 欠損・重複除去
abstracts = df['成果概要（日本語）'].dropna().drop_duplicates().tolist()

#%% トークン数ベースでチャンク分割（上限 8000トークン）
MAX_TOKENS = 8000
chunks = []
current_chunk = []
current_tokens = 0

for abstract in abstracts:
    tokens = count_tokens(abstract)
    if current_tokens + tokens > MAX_TOKENS:
        chunks.append("\n".join(current_chunk))
        current_chunk = [abstract]
        current_tokens = tokens
    else:
        current_chunk.append(abstract)
        current_tokens += tokens

if current_chunk:
    chunks.append("\n".join(current_chunk))

#%% バッチ処理準備・送信
os.makedirs("data", exist_ok=True)
total_batches = len(chunks)

for i, chunk in enumerate(chunks):
    request_data = [{
        "custom_id": f"request-{i}",
        "method": "POST",
        "url": "/v1/chat/completions",
        "body": {
            "model": "gpt-4.1-mini",
            "messages": [
                {
                    "role": "system",
                    "content": "次のテキストから用語を抽出してください。出力は抽出した用語のみ、空白区切りで記述してください。"
                },
                {
                    "role": "user",
                    "content": chunk
                }
            ],
            "max_tokens": 2000
        }
    }]

    jsonl_path = f"data/batch_{i}.jsonl"
    write_jsonl(jsonl_path, request_data)

    batch_input_file = client.files.create(file=open(jsonl_path, "rb"), purpose="batch")
    batch_metadata = client.batches.create(
        input_file_id=batch_input_file.id,
        endpoint="/v1/chat/completions",
        completion_window="24h",
        metadata={"description": "token-based-batch"}
    )

    with open('request_input_id.csv', 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([jsonl_path, batch_metadata.id, batch_input_file.id])

    status = confirm_batch_status(batch_metadata, batch_input_file.id)
    progress = (i + 1) / total_batches * 100
    if status:
        print(f"✅ Batch {batch_metadata.id} has completed. ({progress:.2f}%)")
    else:
        print(f"❌ Batch {batch_metadata.id} has failed. ({progress:.2f}%)")

#%% 結果取得と出力
df_request_batch = pd.read_csv("request_input_id.csv", header=None, names=["input_file", "batch_id", "input_file_id"])
batche_ids = df_request_batch['batch_id'].tolist()

terms_list = []
count = 0
for batch_id in tqdm(batche_ids):
    info = client.batches.retrieve(batch_id)
    if info.status == "completed" and info.output_file_id:
        response = client.files.content(info.output_file_id)
        outputs = [json.loads(line) for line in response.text.strip().split('\n')]
        for o in outputs:
            content = o['response']['body']['choices'][0]['message']['content']
            terms = content.strip().split()
            terms_list.extend(terms)
            count += 1

#%% ファイル出力（重複あり、日時付きファイル名）
timestamp = datetime.now().strftime("%Y%m%d_%H%M")
base_name = os.path.splitext(os.path.basename(FILE_NAME))[0]
output_filename = f"{timestamp}_{base_name}_terms_only.csv"

with open(output_filename, 'w', encoding='utf-8', newline='') as f:
    f.write(','.join(terms_list))

print(f"✅ 用語リストを {output_filename} に出力しました")