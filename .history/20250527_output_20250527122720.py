import csv
import json
import time
import os
from datetime import datetime

import pandas as pd
from openai import OpenAI
from tqdm import tqdm
import tiktoken

#%% 結果取得とCSV出力
df_request_batch = pd.read_csv("data/batch_0.jsonl,batch_68352ac929588190b751e9358b4190cc,file-Mwrn79EWLM63nyD3Wkqeqa", header=None, names=["input_file", "batch_id", "input_file_id"])
batch_ids = df_request_batch['batch_id'].tolist()

output_records = []

for batch_id in tqdm(batch_ids):
    info = client.batches.retrieve(batch_id)
    if info.status == "completed" and info.output_file_id:
        response = client.files.content(info.output_file_id)
        outputs = [json.loads(line) for line in response.text.strip().split('\n')]
        for o in outputs:
            custom_id = o['custom_id']
            index = int(custom_id.replace("request-", ""))
            row = df_filtered.iloc[index]
            content = o['response']['body']['choices'][0]['message']['content'].strip()

            # 出力行を「-」「・」から始まるものだけに絞って抽出
            output_lines = [line.strip("・- ").strip() for line in content.split('\n') if line.strip().startswith(("-", "・"))]

            output_records.append([row.name, row["出現形"], row["正規形"]] + output_lines)

#%% CSV出力
timestamp = datetime.now().strftime("%Y%m%d_%H%M")
output_filename = f"{timestamp}_症状出力結果.csv"

max_outputs = max(len(record) for record in output_records) - 3  # 出力の最大個数
columns = ["行ID", "出現形", "正規形"] + [f"出力{i+1}" for i in range(max_outputs)]

df_output = pd.DataFrame(output_records, columns=columns)
df_output.to_csv(output_filename, index=False, encoding='utf-8-sig')

print(f"✅ 出力結果を {output_filename} に保存しました。")