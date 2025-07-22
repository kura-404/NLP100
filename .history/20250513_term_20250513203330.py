#%%
import csv
import json
import math
import time
import os

import pandas as pd
from openai import OpenAI
from tqdm import tqdm
from datetime import datetime
#%% OpenAIクライアント初期化
client = OpenAI()

#%% バッチ状態確認関数（リトライあり）
def confirm_batch_status(batch_metadata, batch_input_file_id) -> bool:
    batch_status = client.batches.retrieve(batch_metadata.id)

    if batch_status.status == "completed":
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
                metadata={"description": "count word"}
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

#%% ファイル読み込みとリスト作成
FILE_NAME = "/Users/kuramotomana/Test/成果概要.csv"
df = pd.read_csv(FILE_NAME, encoding='utf-8-sig')

# 欠損・重複を除去した研究概要リスト
research_abstracts = df[''].dropna().drop_duplicates().tolist()

#%% 件数ベースでチャンク分割（例：200件ずつ）
CHUNK_SIZE = 200
chunks = [research_abstracts[i:i + CHUNK_SIZE] for i in range(0, len(research_abstracts), CHUNK_SIZE)]

#%% チャンク単位で request_data をファイルごとに分割出力
os.makedirs("data", exist_ok=True)
total_batches = len(chunks)

for i, chunk in enumerate(chunks):
    joined_chunk = "\n".join(chunk)
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
                    "content": joined_chunk
                }
            ],
            "max_tokens": 2000
        }
    }]

    jsonl_path = f"data/batch_{i}.jsonl"
    write_jsonl(jsonl_path, request_data)

    batch_input_file = client.files.create(
        file=open(jsonl_path, "rb"),
        purpose="batch"
    )

    batch_metadata = client.batches.create(
        input_file_id=batch_input_file.id,
        endpoint="/v1/chat/completions",
        completion_window="24h",
        metadata={"description": "chunk-based-batch"}
    )

    with open('request_input_id.csv', 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([jsonl_path, batch_metadata.id, batch_input_file.id])

    # バッチの実行状況を確認
    status = confirm_batch_status(batch_metadata, batch_input_file.id)
    progress = (i + 1) / total_batches * 100
    if status:
        print(f"✅ Batch {batch_metadata.id} has completed. ({progress:.2f}%)")
    else:
        print(f"❌ Batch {batch_metadata.id} has failed. ({progress:.2f}%)")

#%% バッチID一覧を読み込み

df_request_batch = pd.read_csv("request_input_id.csv", header=None, names=["input_file", "batch_id", "input_file_id"])
batche_ids = df_request_batch['batch_id'].tolist()

#%% 結果取得と用語抽出
yomi_outputs = []
count = 0
batch_count = 0
for ids in tqdm(batche_ids):
    batches_information = client.batches.retrieve(ids)
    if batches_information.status == "completed" and batches_information.output_file_id is not None:
        file_response = client.files.content(batches_information.output_file_id)
        output = [json.loads(i) for i in file_response.text.strip().split('\n')]
        for count_in_batch, o in enumerate(output):
            yomi_output = o['response']['body']['choices'][0]['message']['content']
            yomi_outputs.append(yomi_output)
            with open('yomi_outputs.csv', 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([ids, batch_count, count, count_in_batch, yomi_output])
            count += 1
    batch_count += 1

#%% CSVに出力
#%% CSVに出力（日時_元ファイル名_terms_only.csv 形式・カレントディレクトリに出力）


df_output = pd.read_csv("yomi_outputs.csv", header=None, names=["batch_id", "batch_count", "count", "count_in_batch", "yomi_output"])
terms_list = []
for row in df_output['yomi_output']:
    terms_list.extend(row.strip().split())

# 日時とファイル名（拡張子なし）を取得
timestamp = datetime.now().strftime("%Y%m%d_%H%M")
base_name = os.path.splitext(os.path.basename(FILE_NAME))[0]

# 出力ファイル名（カレントディレクトリ）
output_filename = f"{timestamp}_{base_name}_terms_only.csv"

# 書き出し
with open(output_filename, 'w', encoding='utf-8', newline='') as f:
    f.write(','.join(terms_list))

print(f"✅ 用語リストを {output_filename} に出力しました")
