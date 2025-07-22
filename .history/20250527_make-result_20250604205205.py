import os
import json
import time
import random
import tiktoken
import pandas as pd
from datetime import datetime
from openai import OpenAI
from sklearn.metrics.pairwise import cosine_similarity
from tqdm import tqdm
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
    print(f"📦 Batch {batch_id} submitted. Waiting for completion...")
    while True:
        status = client.batches.retrieve(batch_id).status
        if status == "completed":
            print(f"✅ Batch {batch_id} completed.")
            return True
        elif status == "failed":
            print(f"❌ Batch {batch_id} failed.")
            return False
        else:
            print(f"⏳ Batch {batch_id} still {status}... Waiting 30s")
            time.sleep(30)

# 生成元データ読み込み
FILE_PATH = "/Users/kuramotomana/Test/20250602_最新年度.xlsx"
df = pd.read_excel(FILE_PATH)
df_filtered = df[df["対象疾患"].astype(str).str.contains("新生物", na=False)]
df_filtered = df_filtered.dropna(subset=["成果概要（日本語）", "課題管理番号"])

# 埋め込み可能な概要だけ選定
examples_pool = []
for _, row in df_filtered.iterrows():
    text = str(row["成果概要（日本語）"]).strip()
    if count_tokens(text) <= 8192:
        examples_pool.append((row["課題管理番号"], text))

# 100リクエスト分のJSONLを作成（10件ずつ×10バッチ）
os.makedirs("batch_jsonl", exist_ok=True)
os.makedirs("outputs", exist_ok=True)
all_requests = []
for batch_id in range(10):
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

        all_requests.append({
            "custom_id": f"batch{batch_id:02}_req{req_id:02}",
            "method": "POST",
            "url": "/v1/chat/completions",
            "body": {
                "model": "gpt-4.1-mini",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 2000
            }
        })

# 各バッチごとに分割して送信
for i in range(10):
    batch_requests = all_requests[i*10:(i+1)*10]
    jsonl_path = f"batch_jsonl/batch_{i:02}.jsonl"
    write_jsonl(jsonl_path, batch_requests)

    # ファイルアップロードとバッチ送信
    input_file = client.files.create(file=open(jsonl_path, "rb"), purpose="batch")
    batch = client.batches.create(
        input_file_id=input_file.id,
        endpoint="/v1/chat/completions",
        completion_window="24h"
    )

    if wait_for_batch_completion(batch.id):
        content_file = client.files.content(batch.output_file_id)
        lines = content_file.text.strip().split('\n')

        for line in lines:
            res = json.loads(line)
            gen_text = res['response']['body']['choices'][0]['message']['content'].strip()
            req_id = res["custom_id"]

            # 類似検索
            gen_emb = get_embedding(gen_text)
            emb_refs = [get_embedding(txt) for _, txt in examples_pool]
            sims = cosine_similarity([gen_emb], emb_refs)[0]
            idx = int(np.argmax(sims))
            most_sim_id, most_sim_text = examples_pool[idx]
            diff_text = "\n".join(difflib.ndiff(gen_text.split(), most_sim_text.split()))

            # 保存
            with open(f"outputs/{req_id}.txt", "w", encoding="utf-8") as f_txt:
                f_txt.write(gen_text)

            df_out = pd.DataFrame([{
                "リクエストID": req_id,
                "生成された成果概要": gen_text,
                "最も類似した成果概要": most_sim_text,
                "課題管理番号": most_sim_id,
                "類似度": sims[idx],
                "差分": diff_text
            }])
            df_out.to_csv(f"outputs/{req_id}_比較.csv", index=False, encoding="utf-8-sig")
    else:
        print(f"❌ Failed batch {i}")