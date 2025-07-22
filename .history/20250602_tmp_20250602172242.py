import csv
import json
import re
import os
from datetime import datetime

import pandas as pd
from openai import OpenAI
from tqdm import tqdm

#%% クライアント初期化
client = OpenAI()

#%% 出力分割関数（番号付きにも対応）
def split_numbered_responses(text):
    parts = re.split(r'\s*\d+\.\s*', text.strip())
    return [part for part in parts if part]

#%% ファイル読み込み（バッチID一覧と入力データ）
request_id_filename = "/Users/kuramotomana/Test/request_input_id_20250602_154413.csv"
FILE_NAME = "/Users/kuramotomana/Test/DISEASE_mini.xlsx"

df = pd.read_excel(FILE_NAME)
df = df.iloc[1:]
df_filtered = df[
    (df["出現形"].notna()) &
    (df["正規形"].notna()) &
    (~df["正規形"].astype(str).str.strip().isin(["-1", "ERR"]))
].head(100).reset_index(drop=True).copy()

df_request_batch = pd.read_csv(request_id_filename, header=None, names=["input_file", "batch_id", "input_file_id"])
batch_ids = df_request_batch['batch_id'].tolist()

#%% 出力取得と整形
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

            output_lines = [line.strip("・- 「」\"").strip() for line in content.split('\n') if line.strip().startswith(("-", "・"))]
            if not output_lines:
                output_lines = split_numbered_responses(content.strip())
                output_lines = [line.strip("・- 「」\"").strip() for line in output_lines if line.strip()]

            # ✅ 行ID, ID, 出現形, 正規形を含める
            output_records.append([row["行ID"], row["ID"], row["出現形"], row["正規形"]] + output_lines)

#%% CSVに保存
timestamp = datetime.now().strftime("%Y%m%d_%H%M")
output_filename = f"{timestamp}_症状出力結果_full.csv"

max_outputs = max(len(record) for record in output_records) - 4  # 4列分が固定情報
columns = ["行ID", "ID", "出現形", "正規形"] + [f"出力{i+1}" for i in range(max_outputs)]

df_output = pd.DataFrame(output_records, columns=columns)
df_output.to_csv(output_filename, index=False, encoding='utf-8-sig')

print(f"✅ 出力結果を {output_filename} に保存しました。")