#%%
import csv
import json
import time
import os

import pandas as pd
import tiktoken
from openai import OpenAI

#%% OpenAIクライアント初期化
client = OpenAI()

#%% トークンカウント関数（gpt-4.1-mini）
encoding = tiktoken.encoding_for_model("gpt-4.1-mini")
def count_tokens(text: str) -> int:
    return len(encoding.encode(text))

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

#%% ファイル読み込みとチャンク分割
FILE_NAME = "/Users/kuramotomana/Test/全課題データ抽出.csv"
df = pd.read_csv(FILE_NAME, encoding='utf-8-sig')

research_abstracts = df['研究概要'].dropna().drop_duplicates().tolist()

MAX_TOKENS = 2000
chunks = []
current_chunk = ""
current_tokens = 0

for abstract in research_abstracts:
    abstract = abstract.strip()
    t = count_tokens(abstract)
    if current_tokens + t > MAX_TOKENS:
        chunks.append(current_chunk.strip())
        current_chunk = abstract + "\n"
        current_tokens = t
    else:
        current_chunk += abstract + "\n"
        current_tokens += t

if current_chunk.strip():
    chunks.append(current_chunk.strip())
print(f"✅ チャンク数: {len(chunks)}")にゅう

#%% request_dataを作成
request_data = []
for i, chunk in enumerate(chunks):
    request = {
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
    }
    request_data.append(request)

#%% JSONLファイルに書き出し
os.makedirs("data", exist_ok=True)
jsonl_path = "data/batch_split.jsonl"
write_jsonl(jsonl_path, request_data)
print(f"✅ JSONL書き出し完了: {jsonl_path}")

#%% バッチ送信
batch_input_file = client.files.create(
    file=open(jsonl_path, "rb"),
    purpose="batch"
)
batch_input_file_id = batch_input_file.id

batch_metadata = client.batches.create(
    input_file_id=batch_input_file_id,
    endpoint="/v1/chat/completions",
    completion_window="24h",
    metadata={"description": "split-token-batch"}
)

with open('request_input_id.csv', 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(["batch_split.jsonl", batch_metadata.id, batch_input_file_id])

#%% バッチ完了待機
status = confirm_batch_status(batch_metadata, batch_input_file_id)
if not status:
    print(f"Batch {batch_metadata.id} failed even after retries.")
    exit()

#%% 出力取得と結合
batches_information = client.batches.retrieve(batch_metadata.id)
file_response = client.files.content(batches_information.output_file_id)
output = [json.loads(i) for i in file_response.text.strip().split('\n')]

terms_list = []
for o in output:
    content = o['response']['body']['choices'][0]['message']['content']
    terms = content.strip().split()
    terms_list.extend(terms)

#%% 重複を除かずにCSV保存
with open(f"{FILE_NAME}_terms_only.csv", 'w', encoding='utf-8', newline='') as f:
    f.write(','.join(terms_list))

print(f"✅ 用語リストを {FILE_NAME}_terms_only.csv に出力しました")