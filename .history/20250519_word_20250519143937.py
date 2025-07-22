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

#%% 結果取得と出力
df_request_batch = pd.read_csv("/Users/kuramotomana/Test/20250519_request.csv", header=None, names=["input_file", "batch_id", "input_file_id"])
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
output_filename = f"{timestamp}_{base_name}_terms_only.csv"

with open(output_filename, 'w', encoding='utf-8', newline='') as f:
    f.write(','.join(terms_list))

print(f"✅ 用語リストを {output_filename} に出力しました")