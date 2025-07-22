import os
import json
import time
import random
import tiktoken
import pandas as pd
import numpy as np
from datetime import datetime
from openai import OpenAI
from sklearn.metrics.pairwise import cosine_similarity
import difflib

# OpenAI クライアント初期化
client = OpenAI()

# トークンエンコーダ
encoding = tiktoken.get_encoding("cl100k_base")
def count_tokens(text: str) -> int:
    return len(encoding.encode(text))

# 埋め込み取得関数（8192トークンまで）
def get_embedding(text: str, max_tokens: int = 8192) -> list:
    tokens = encoding.encode(text)
    if len(tokens) > max_tokens:
        tokens = tokens[:max_tokens]
    trimmed = encoding.decode(tokens)
    response = client.embeddings.create(
        input=[trimmed],
        model="text-embedding-3-small"
    )
    return response.data[0].embedding

# JSONL書き出し
def write_jsonl(filename, data):
    with open(filename, 'w', encoding='utf-8') as f:
        for entry in data:
            json.dump(entry, f, ensure_ascii=False)
            f.write('\n')

# バッチ進捗確認
def wait_for_batch_completion(batch_id):
    print(f"\U0001F4E6 Batch {batch_id} submitted. Waiting for completion...")
    while True:
        status = client.batches.retrieve(batch_id).status
        if status == "completed":
            print(f"✅ Batch {batch_id} completed.")
            return True
        elif status == "failed":
            print(f"❌ Batch {batch_id} failed.")
            return False
        else:
            print(f"⏳ Batch {batch_id} still {status}... Waiting 60s")
            time.sleep(60)

# データ読み込み
FILE_PATH = "/Users/kuramotomana/Test/20250602_最新年度.xlsx"
df = pd.read_excel(FILE_PATH)
df_filtered = df[df["対象疾患"].astype(str).str.contains("新生物", na=False)]
df_filtered = df_filtered.dropna(subset=["成果概要（日本語）", "課題管理番号"])

# トークン制限内のデータのみ抽出
examples_pool = []
for _, row in df_filtered.iterrows():
    text = str(row["成果概要（日本語）"]).strip()
    if count_tokens(text) <= 8192:
        examples_pool.append((row["課題管理番号"], text))

# 出力用ディレクトリ作成
os.makedirs("batch_jsonl", exist_ok=True)
os.makedirs("outputs", exist_ok=True)

# === 1バッチ（10リクエスト）を構築 ===
batch_id = 0
dt_str = datetime.now().strftime("%Y%m%d_%H%M%S")
all_requests = []
used_examples_map = {}

for req_id in range(10):
    random.shuffle(examples_pool)
    prompt_examples = ""
    total_tokens = 0
    used = []
    for ex_id, ex_text in examples_pool:
        line = f"- {ex_text}\n"
        tokens = count_tokens(line)
        if total_tokens + tokens > 125000:
            break
        prompt_examples += line
        total_tokens += tokens
        used.append((ex_id, ex_text))

    prompt = f"""
以下は研究成果概要の実例です。
これらを参考に、新たな架空の成果概要を1件だけ作成してください。

{prompt_examples}
    """.strip()

    custom_id = f"batch{batch_id:02}_req{req_id:02}"
    used_examples_map[custom_id] = used

    all_requests.append({
        "custom_id": custom_id,
        "method": "POST",
        "url": "/v1/chat/completions",
        "body": {
            "model": "gpt-4.1-mini",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 2000
        }
    })

# JSONL化して送信
jsonl_path = f"batch_jsonl/batch_{batch_id:02}.jsonl"
write_jsonl(jsonl_path, all_requests)

input_file = client.files.create(file=open(jsonl_path, "rb"), purpose="batch")
batch = client.batches.create(
    input_file_id=input_file.id,
    endpoint="/v1/chat/completions",
    completion_window="24h"
)

# バッチ完了待ち
if wait_for_batch_completion(batch.id):
    batch_info = client.batches.retrieve(batch.id)
    if not batch_info.output_file_id:
        print(f"⚠️ Batch {batch.id} completed, but output_file_id is None. Skipping.")
    else:
        content_file = client.files.content(batch_info.output_file_id)
        lines = content_file.text.strip().split('\n')

        for line in lines:
            res = json.loads(line)
            req_id = res.get("custom_id", "unknown")

            try:
                gen_text = res["response"]["body"]["choices"][0]["message"]["content"].strip()
            except (KeyError, IndexError):
                print(f"⚠️ Skipping {req_id}: missing choices or content.")
                continue

            # 使用した比較対象に対して類似度計算
            examples_used = used_examples_map.get(req_id, [])
            if not examples_used:
                print(f"⚠️ No examples found for {req_id}. Skipping.")
                continue

            gen_emb = get_embedding(gen_text)
            emb_refs = [get_embedding(txt) for _, txt in examples_used]
            sims = cosine_similarity([gen_emb], emb_refs)[0]
            idx = int(np.argmax(sims))
            most_sim_id, most_sim_text = examples_used[idx]
            diff_text = "\n".join(difflib.ndiff(gen_text.split(), most_sim_text.split()))

            # 保存（バッチ情報付きファイル名）
            txt_path = f"outputs/{dt_str}_{req_id:02}_batch{batch_id:02}_req{req_id:02}.txt"
            csv_path = f"outputs/{dt_str}_{req_id:02}_batch{batch_id:02}_req{req_id:02}_比較.csv"

            with open(txt_path, "w", encoding="utf-8") as f_txt:
                f_txt.write(gen_text)

            df_out = pd.DataFrame([{
                "リクエストID": req_id,
                "生成された成果概要": gen_text,
                "最も類似した成果概要": most_sim_text,
                "課題管理番号": most_sim_id,
                "類似度": sims[idx],
                "差分": diff_text,
                "参考件数": len(examples_used)
            }])
            df_out.to_csv(csv_path, index=False, encoding="utf-8-sig")

            print(f"✅ {req_id} saved.")
else:
    print(f"❌ Failed batch {batch_id}")
