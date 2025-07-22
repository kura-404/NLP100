#%%
import csv
import json
import math
import time
import os
from collections import OrderedDict
from datetime import datetime

import pandas as pd
from openai import OpenAI
from tqdm import tqdm

#%%
client = OpenAI()

# 出力先ディレクトリ
DATA_DIR = "data"
OUTPUT_DIR = "outputs"
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
output_csv_path = f"{OUTPUT_DIR}/terms_output_{timestamp}.csv"
yomi_output_log = f"{OUTPUT_DIR}/yomi_outputs.csv"
batch_record_path = f"{OUTPUT_DIR}/request_input_id.csv"

#%%
def confirm_batch_status(batch_metadata, batch_input_file_id, max_retries=5, wait_time=60) -> bool:
    """バッチの状態を確認し、必要に応じてリトライ・待機"""
    batch_status = client.batches.retrieve(batch_metadata.id)
    
    if batch_status.status == "completed":
        return True
    elif batch_status.status == "failed":
        print(f"Batch {batch_metadata.id} has failed.")
        retry_count = 0
        while batch_status.status == "failed" and retry_count < max_retries:
            retry_count += 1
            batch_metadata = client.batches.create(
                input_file_id=batch_input_file_id,
                endpoint="/v1/chat/completions",
                completion_window="24h",
                metadata={"description": "count word"}
            )
            batch_status = client.batches.retrieve(batch_metadata.id)
        return batch_status.status == "completed"

    while batch_status.status != "completed":
        time.sleep(wait_time)
        batch_status = client.batches.retrieve(batch_metadata.id)
    return batch_status.status == "completed"

def write_jsonl(filename, data):
    with open(filename, 'w', encoding='utf-8') as f:
        for entry in data:
            json.dump(entry, f, ensure_ascii=False)
            f.write('\n')

def create_requests(start_idx, batch_size, texts):
    requests = []
    actual_texts = texts[start_idx:start_idx + batch_size]
    for i, text in enumerate(actual_texts):
        request = {
            "custom_id": f"request-{start_idx + i}",
            "method": "POST",
            "url": "/v1/chat/completions",
            "body": {
                "model": "gpt-4.1-mini",
                "messages": [
                    {"role": "system", "content": "次のテキストから用語を抽出してください．出力は抽出した用語のみとしてください．"},
                    {"role": "user", "content": text}
                ],
                "max_tokens": 2000
            }
        }
        requests.append(request)
    return requests

def append_output_row(row_data, filename=yomi_output_log):
    with open(filename, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(row_data)

#%%
# ファイル読み込みとデータ準備
FILE_NAME = "/Users/kuramotomana/Test/テスト用データ.xlsx"
df = pd.read_excel(FILE_NAME)
research_abstract = df['研究概要'].tolist()
result_abstract = df['成果概要（日本語）'].tolist()

# ユニーク化
all_texts = list(OrderedDict.fromkeys(research_abstract + result_abstract))

#%%
# JSONL作成
BATCH_SIZE = 2000
total_batches = math.ceil(len(all_texts) / BATCH_SIZE)

for i in range(total_batches):
    request_data = create_requests(i * BATCH_SIZE, BATCH_SIZE, all_texts)
    write_jsonl(f"{DATA_DIR}/batch_{i}.jsonl", request_data)

#%%
# バッチ投入とログ記録
for i in tqdm(range(total_batches), desc="Uploading Batches"):
    batch_input_file = client.files.create(
        file=open(f"{DATA_DIR}/batch_{i}.jsonl", "rb"),
        purpose="batch"
    )
    batch_input_file_id = batch_input_file.id

    batch_metadata = client.batches.create(
        input_file_id=batch_input_file_id,
        endpoint="/v1/chat/completions",
        completion_window="24h",
        metadata={"description": "count word"}
    )

    with open(batch_record_path, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([f"batch_{i}.jsonl", batch_metadata.id, batch_input_file_id])

    if confirm_batch_status(batch_metadata, batch_input_file_id):
        print(f"Batch {batch_metadata.id} completed.")
    else:
        print(f"Batch {batch_metadata.id} failed.")

#%%
# 出力収集
df_request_batch = pd.read_csv(batch_record_path, header=None, names=["input_file", "batch_id", "input_file_id"])
batche_ids = df_request_batch['batch_id'].tolist()
yomi_outputs = []
count = 0
batch_count = 0

for batch_id in tqdm(batche_ids, desc="Collecting Outputs"):
    batch_info = client.batches.retrieve(batch_id)
    if batch_info.status != "completed" or batch_info.output_file_id is None:
        continue

    file_response = client.files.content(batch_info.output_file_id)
    output = [json.loads(i) for i in file_response.text.strip().split('\n')]

    for count_in_batch, o in enumerate(output):
        yomi_output = o['response']['body']['choices'][0]['message']['content']
        yomi_outputs.append(yomi_output)
        append_output_row([batch_id, batch_count, count, count_in_batch, yomi_output])
        count += 1
    batch_count += 1

#%%
# CSVとして保存
df_terms = pd.DataFrame({'extracted_terms': yomi_outputs})
df_terms.to_csv(output_csv_path, index=False)
print(f"✅ 用語抽出結果を保存しました: {output_csv_path}")