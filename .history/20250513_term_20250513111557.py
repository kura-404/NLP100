#%%
import csv
import json
import time

import pandas as pd
from openai import OpenAI

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

#%% ファイル読み込みと結合
FILE_NAME = "/Users/kuramotomana/Test/全課題データ抽出.csv"
df = pd.read_csv(FILE_NAME, encoding='utf-8-sig')

# 研究概要を結合（重複除去・欠損除去）
research_abstract = df['研究概要'].dropna().drop_duplicates().tolist()
combined_text = "\n".join(research_abstract)

#%% 単一リクエスト分のJSONLを作成
request_data = [{
    "custom_id": "request-0",
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
                "content": combined_text
            }
        ],
        "max_tokens": 2000
    }
}]
write_jsonl("data/batch_all.jsonl", request_data)

#%% バッチ送信
batch_input_file = client.files.create(
    file=open("data/batch_all.jsonl", "rb"),
    purpose="batch"
)
batch_input_file_id = batch_input_file.id

batch_metadata = client.batches.create(
    input_file_id=batch_input_file_id,
    endpoint="/v1/chat/completions",
    completion_window="24h",
    metadata={"description": "count word"}
)

with open('request_input_id.csv', 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(["batch_all.jsonl", batch_metadata.id, batch_input_file_id])

# バッチ完了待機
status = confirm_batch_status(batch_metadata, batch_input_file_id)
if not status:
    print(f"Batch {batch_metadata.id} failed even after retries.")
    exit()

#%% 出力取得
batches_information = client.batches.retrieve(batch_metadata.id)
file_response = client.files.content(batches_information.output_file_id)

# 応答の取り出し
output = [json.loads(i) for i in file_response.text.strip().split('\n')]
terms_string = output[0]['response']['body']['choices'][0]['message']['content']
terms_list = terms_string.strip().split()

#%% 重複を除かずにCSV保存
with open(f"{FILE_NAME}_terms_only.csv", 'w', encoding='utf-8', newline='') as f:
    f.write(','.join(terms_list))