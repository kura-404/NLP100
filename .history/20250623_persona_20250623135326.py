#患者のペルソナを設定して、辞書の上位100件について患者表現を生成する
import csv
import json
import time
import os
from datetime import datetime
import re

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
                input_file_id=batch_input_file.id,
                endpoint="/v1/chat/completions",
                completion_window="24h",
                metadata={"description": "retry"}
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

#%% 出力を番号付きで分割する関数
def split_numbered_responses(text):
    parts = re.split(r'\s*\d+\.\s*', text.strip())
    return [part for part in parts if part]

#%% ファイル読み込みとリクエスト生成
FILE_NAME = "/Users/kuramotomana/Test/DISEASE_mini.xlsx"
df = pd.read_excel(FILE_NAME)

# タイトル行を除く → 欠損・不正な正規形（-1, ERR）を除く
df = df.iloc[1:]
df_filtered = df[
    (df["出現形"].notna()) &
    (df["正規形"].notna()) &
    (~df["正規形"].astype(str).str.strip().isin(["-1", "ERR"]))
].head(100).reset_index(drop=True).copy()

# 指示文
INSTRUCTION = """# Instructions
あなたは病院の外来を受診した患者です。以下の「出現形」と「正規形」（医療用語）を参考に、医師に自分の症状を自然な言葉で伝えてください。
- 「どこが」「どんなとき」「どんなふうに」「どんなきっかけで」など、症状の場所、状況、感じ方も自由に加えてください。
-  誰かの話ではなく、自分の症状として話してください。
-  医療用語は使わず、家族や友人に話すような言い回しにしてください。
-  ３パターン作成してください。

# Examples
Input:
出現形: できものができている
正規形: 皮下腫瘤

Output:
- 「腕に小さいできものができて、押すとちょっと痛いです」
- 「首の後ろにしこりみたいなものができて、不安です」
"""

# 1レコード = 1リクエスト形式で作成
all_requests = []
for i, (row_index, row) in enumerate(df_filtered.iterrows()):
    all_requests.append({
        "custom_id": f"request-{i}",
        "method": "POST",
        "url": "/v1/chat/completions",
        "body": {
            "model": "gpt-4.1-mini",
            "messages": [
                {
                    "role": "system", "content": "あなたは日本の子どもです。"
                },
                {
                    "role": "user",
                    "content": INSTRUCTION + f"\n\n# Input:\n出現形: {row['出現形']}\n正規形: {row['正規形']}"
                }
            ],
            "max_tokens": 2000
        }
    })

#%% 100件ずつバッチ送信
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
request_id_filename = f"request_input_id_{timestamp}.csv"
os.makedirs("data", exist_ok=True)
total_batches = (len(all_requests) + 99) // 100

for i in range(total_batches):
    batch_requests = all_requests[i*100:(i+1)*100]
    jsonl_path = f"data/batch_{i}.jsonl"
    write_jsonl(jsonl_path, batch_requests)

    batch_input_file = client.files.create(file=open(jsonl_path, "rb"), purpose="batch")
    batch_metadata = client.batches.create(
        input_file_id=batch_input_file.id,
        endpoint="/v1/chat/completions",
        completion_window="24h",
        metadata={"description": "record-based-batch"}
    )

    with open(request_id_filename, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([jsonl_path, batch_metadata.id, batch_input_file.id])

    status = confirm_batch_status(batch_metadata, batch_input_file.id)
    processed_requests = min((i + 1) * 100, len(all_requests))
    progress = processed_requests / len(all_requests) * 100

    if status:
        print(f"✅ Batch {batch_metadata.id} has completed. ({progress:.2f}%)")
    else:
        print(f"❌ Batch {batch_metadata.id} has failed. ({progress:.2f}%)")

#%% 結果取得とCSV出力
df_request_batch = pd.read_csv(request_id_filename, header=None, names=["input_file", "batch_id", "input_file_id"])
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

            output_lines = [line.strip("・- 「」\"").strip() for line in content.split('\n') if line.strip().startswith(("-", "・"))]
            if not output_lines:
                output_lines = split_numbered_responses(content.strip())
                output_lines = [line.strip("・- 「」\"").strip() for line in output_lines if line.strip()]

            # ✅ 元データの「行ID」「ID」列を含めて記録
            output_records.append([
                row["行ID"],
                row["ID"],
                row["出現形"],
                row["正規形"]
            ] + output_lines)

#%% CSV出力
timestamp = datetime.now().strftime("%Y%m%d_%H%M")
output_filename = f"{timestamp}_症状出力結果.csv"

max_outputs = max(len(record) for record in output_records) - 4  # 出力の最大個数（行ID, ID, 出現形, 正規形を除く）
columns = ["行ID", "ID", "出現形", "正規形"] + [f"出力{i+1}" for i in range(max_outputs)]

df_output = pd.DataFrame(output_records, columns=columns)
df_output.to_csv(output_filename, index=False, encoding='utf-8-sig')

print(f"✅ 出力結果を {output_filename} に保存しました。")
