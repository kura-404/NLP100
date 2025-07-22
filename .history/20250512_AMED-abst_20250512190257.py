#%%
import csv
import json
import math
import time

import pandas as pd
from openai import OpenAI
from tqdm import tqdm

#%%


def confirm_batch_status(batch_metadata, batch_input_file_id)->bool:
    """ バッチの状態を確認し、エラーの場合はリトライする 
    """
# バッチの状態を取得
    batch_status = client.batches.retrieve(batch_metadata.id)
                
    # 完了していたら次のバッチへ
    if batch_status.status == "completed":
        return True
    # 失敗していたらログ出してリトライ
    elif batch_status.status == "failed":
        print(f"Batch {batch_metadata.id} has failed.")
        # リトライ
        retry_count = 0
        max_retries = 5
        while batch_status.status == "failed" and retry_count < max_retries:
            retry_count += 1
            batch_metadata = client.batches.create(
                input_file_id=batch_input_file_id,
                endpoint="/v1/chat/completions",
                completion_window="24h",
                metadata={
                    "description": "count word"
                }
            )
            batch_status = client.batches.retrieve(batch_metadata.id)
        return True if batch_status.status == "completed" else False
    
    # 完了していない場合、完了するまで待機 
    while batch_status.status != "completed":
        time.sleep(60)
        batch_status = client.batches.retrieve(batch_metadata.id)
    return True if batch_status.status == "completed" else False

# JSONLファイルの書き込み関数
def write_jsonl(filename, data):
    with open(filename, 'w', encoding='utf-8') as f:
        for entry in data:
            json.dump(entry, f, ensure_ascii=False)
            f.write('\n')

# リクエストデータを生成する関数
def create_requests(str_pos_request, num_requests, texts):
    requests = []
    remainder = len(texts) % num_requests
    if len(texts) < num_requests + str_pos_request:
        num_requests = remainder
    for i in range(num_requests):
        text = texts[i+ str_pos_request]
        request = {
            "custom_id": f"request-{i+ str_pos_request}",
            "method": "POST",
            "url": "/v1/chat/completions",
            "body": {
                "model": "gpt-4.1-mini",
                "messages": [
                    {"role": "system", "content": """
                     次のテキストから用語を抽出してください．
                     出力は抽出した用語のみとしてください．
                     """},
                    {"role": "user", "content": text}
                ],
                "max_tokens": 2000
            }
        }
        requests.append(request)
    return requests

#%%
FILE_NAME = "/Users/kuramotomana/Test/全課題データ抽出.csv"
df = pd.read_csv(FILE_NAME, encoding='utf-8-sig')
# データの準備
research_abstract = df['研究概要'].dropna().tolist()
all_texts = research_abstract

#%%
BATCH_SIZE = 2000
total_batches = math.ceil(len(all_texts) / BATCH_SIZE)
#%%
for i in range(0, total_batches):
    request_data = create_requests(i*BATCH_SIZE, BATCH_SIZE, all_texts)
    
    # JSONLファイルに書き出し
    write_jsonl(f'data/batch_{i}.jsonl', request_data)

#%%
# .envファイルの内容を読み込む
#load_dotenv(dotenv_path='.env', override=True)
#OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", None)
client = OpenAI()


#%%
#バッチで推論実施
for i in tqdm(range(0, total_batches)):
    batch_input_file = client.files.create(
      file=open(f"data/batch_{i}.jsonl", "rb"),
      purpose="batch"
    )

    batch_input_file_id = batch_input_file.id

    batch_metadata = client.batches.create(
        input_file_id=batch_input_file_id,
        endpoint="/v1/chat/completions",
        completion_window="24h",
        metadata={
          "description": "count word"
        }
    )
    
    with open('request_input_id.csv', 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([f"batch_{i}.jsonl", batch_metadata.id, batch_input_file_id])

    # バッチの実行状況を確認
    status = confirm_batch_status(batch_metadata, batch_input_file_id)
    if status:
        print(f"Batch {batch_metadata.id} has completed.")
        continue
    else:
        print(f"Batch {batch_metadata.id} has failed.")
        

#%%

df_request_batch = pd.read_csv("request_input_id.csv", header=None, names=["input_file", "batch_id", "input_file_id"])

#%%
batche_ids = df_request_batch['batch_id'].tolist()
yomi_outputs = []
count = 0
batch_count = 0
for ids in tqdm(batche_ids):
    
    batches_information = client.batches.retrieve(ids)
    if batches_information.status == "completed":
        if batches_information.output_file_id is not None:
            file_response = client.files.content(batches_information.output_file_id)
    else:
        continue
    output = [json.loads(i) for i in file_response.text.strip().split('\n')]
    for count_in_batch, o in enumerate(output):
        
        yomi_output = o['response']['body']['choices'][0]['message']['content']
        #yomi_output = yomi_output.replace("「", "").replace("」", "")
        yomi_outputs.append(yomi_output)
        with open('yomi_outputs.csv', 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([ids,batch_count, count, count_in_batch, yomi_output])
        count += 1
    batch_count += 1


#%%
df_output = pd.read_csv("yomi_outputs.csv", header=None, names=["batch_id", "batch_count", "count", "count_in_batch", "yomi_output"])

# 単語をすべて結合 → 空白で分割 → 重複除去
all_terms = []
for row in df_output['yomi_output']:
    terms = row.strip().split()
    all_terms.extend(terms)

unique_terms = sorted(set(all_terms))  # 重複除去してソート

# カンマ区切りの1行として出力（ヘッダーなし）
with open(f"{FILE_NAME}_terms_only.csv", 'w', encoding='utf-8', newline='') as f:
    f.write(','.join(unique_terms))