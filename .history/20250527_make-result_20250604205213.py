import pandas as pd
import tiktoken
import json
import random
import time
import os
from datetime import datetime

# OpenAIクライアント初期化
from openai import OpenAI
client = OpenAI()

# トークンエンコーダ
encoding = tiktoken.get_encoding("cl100k_base")
def count_tokens(text: str) -> int:
    return len(encoding.encode(text))

# 設定
MAX_INPUT_TOKENS = 125000
MAX_OUTPUT_TOKENS = 2000
FILE_PATH = "/Users/kuramotomana/Test/20250602_最新年度.xlsx"
TXT_OUT_DIR = "txt_outputs"
CSV_OUT_FILE = f"{datetime.now().strftime('%Y%m%d_%H%M')}_成果比較結果.csv"
os.makedirs(TXT_OUT_DIR, exist_ok=True)

# データ読み込みと事前フィルタリング
df = pd.read_excel(FILE_PATH)
df = df[df["対象疾患"].astype(str).str.contains("新生物", na=False)]
df = df.dropna(subset=["成果概要（日本語）", "課題管理番号"])
df["成果トークン"] = df["成果概要（日本語）"].apply(lambda x: count_tokens(str(x)))
df = df[df["成果トークン"] <= 8192].copy()
df = df[["課題管理番号", "成果概要（日本語）"]].reset_index(drop=True)

# バッチ作成
def create_prompt(examples):
    body = "\n".join([f"- {ex}" for ex in examples])
    return f"""以下は研究成果概要の実例です。
これらを参考に、新たな架空の成果概要を1件だけ作成してください。

{body}
"""

def prepare_batch_requests(df, total_batches=10, requests_per_batch=10):
    all_requests = []
    for batch_idx in range(total_batches):
        for req_idx in range(requests_per_batch):
            seed_df = df.sample(frac=1).reset_index(drop=True)
            example_texts = []
            used = []
            token_sum = 0
            for i, row in seed_df.iterrows():
                example = str(row["成果概要（日本語）"]).strip()
                tokens = count_tokens(f"- {example}\n")
                if token_sum + tokens > MAX_INPUT_TOKENS:
                    break
                token_sum += tokens
                example_texts.append(example)
                used.append((row["課題管理番号"], example))
            prompt = create_prompt(example_texts)
            custom_id = f"batch{batch_idx:02}_req{req_idx:02}"
            all_requests.append({
                "custom_id": custom_id,
                "method": "POST",
                "url": "/v1/chat/completions",
                "body": {
                    "model": "gpt-4.1-mini",
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": MAX_OUTPUT_TOKENS
                },
                "meta_examples": used  # 独自キーで使用例を保存
            })
    return all_requests

# JSONLとMeta保存
def write_jsonl_and_meta(all_requests):
    jsonl_data = []
    meta_map = {}
    for req in all_requests:
        jsonl_data.append({
            "custom_id": req["custom_id"],
            "method": req["method"],
            "url": req["url"],
            "body": req["body"]
        })
        meta_map[req["custom_id"]] = req["meta_examples"]
    jsonl_path = "batch_requests.jsonl"
    with open(jsonl_path, "w", encoding="utf-8") as f:
        for line in jsonl_data:
            json.dump(line, f, ensure_ascii=False)
            f.write("\n")
    return jsonl_path, meta_map

# 類似度＆差分計算
from sklearn.metrics.pairwise import cosine_similarity
import difflib
def get_embedding(text: str) -> list:
    tokens = encoding.encode(text)
    if len(tokens) > 8192:
        tokens = tokens[:8192]
    trimmed = encoding.decode(tokens)
    resp = client.embeddings.create(input=[trimmed], model="text-embedding-3-small")
    return resp.data[0].embedding

def compute_similarity_and_diff(generated: str, examples):
    emb_gen = get_embedding(generated)
    emb_refs = [get_embedding(text) for _, text in examples]
    sims = cosine_similarity([emb_gen], emb_refs)[0]
    idx = int(sims.argmax())
    sim_score = sims[idx]
    ref_id, ref_text = examples[idx]
    diff = list(difflib.ndiff(generated.split(), ref_text.split()))
    return ref_id, ref_text, sim_score, " ".join(diff)

# バッチ送信と結果処理
def run_batch(jsonl_path, meta_map):
    input_file = client.files.create(file=open(jsonl_path, "rb"), purpose="batch")
    batch = client.batches.create(
        input_file_id=input_file.id,
        endpoint="/v1/chat/completions",
        completion_window="24h",
        metadata={"description": "成果概要生成バッチ"}
    )
    print(f"🚀 Batch ID: {batch.id}")

    # 待機
    while True:
        status = client.batches.retrieve(batch.id)
        if status.status == "completed":
            break
        elif status.status == "failed":
            raise RuntimeError(f"❌ Batch {batch.id} failed.")
        time.sleep(60)

    # 結果取得
    resp = client.files.content(status.output_file_id)
    outputs = [json.loads(line) for line in resp.text.strip().split("\n")]

    # 出力処理
    results = []
    for entry in outputs:
        custom_id = entry["custom_id"]
        generated = entry["response"]["body"]["choices"][0]["message"]["content"].strip()
        examples = meta_map[custom_id]
        ref_id, ref_text, score, diff = compute_similarity_and_diff(generated, examples)

        # txt出力
        txt_path = os.path.join(TXT_OUT_DIR, f"{custom_id}_生成成果.txt")
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(generated)

        # csv記録
        results.append([
            custom_id,
            generated,
            ref_id,
            ref_text,
            f"{score:.4f}",
            diff
        ])
    return results

# 実行本体
def main():
    all_requests = prepare_batch_requests(df)
    jsonl_path, meta_map = write_jsonl_and_meta(all_requests)
    results = run_batch(jsonl_path, meta_map)

    # CSV出力
    df_out = pd.DataFrame(results, columns=[
        "custom_id", "生成成果概要", "類似成果_課題管理番号", "類似成果", "類似度", "差分"
    ])
    df_out.to_csv(CSV_OUT_FILE, index=False, encoding="utf-8-sig")
    print(f"✅ 比較結果をCSVに保存しました: {CSV_OUT_FILE}")

if __name__ == "__main__":
    main()