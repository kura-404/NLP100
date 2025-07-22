import pandas as pd
import tiktoken
import json
import random
import time
import difflib
from openai import OpenAI
from datetime import datetime
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import os

# OpenAIクライアント初期化
client = OpenAI()

# トークンエンコーダ
encoding = tiktoken.get_encoding("cl100k_base")
def count_tokens(text: str) -> int:
    return len(encoding.encode(text))

# トークン制限内で埋め込み生成
def get_embedding(text: str, max_tokens: int = 8192) -> list:
    tokens = encoding.encode(text)
    if len(tokens) > max_tokens:
        tokens = tokens[:max_tokens]
    trimmed_text = encoding.decode(tokens)
    response = client.embeddings.create(
        input=[trimmed_text],
        model="text-embedding-3-small"
    )
    return response.data[0].embedding

# バッチ送信＋リトライ付き
def send_batch_with_retry(requests, retries=10, wait=60):
    for attempt in range(retries):
        try:
            # JSONLファイルに保存
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            input_path = f"batch_input_{timestamp}.jsonl"
            with open(input_path, "w", encoding="utf-8") as f:
                for item in requests:
                    json.dump(item, f, ensure_ascii=False)
                    f.write("\n")

            # アップロード
            upload = client.files.create(file=open(input_path, "rb"), purpose="batch")
            batch = client.batches.create(
                input_file_id=upload.id,
                endpoint="/v1/chat/completions",
                completion_window="24h",
                metadata={"description": "generate summary"}
            )

            batch_id = batch.id
            print(f"✅ Batch ID: {batch_id}")
            print("⏳ バッチの完了を待機中...")

            while True:
                status = client.batches.retrieve(batch_id)
                if status.status == "completed":
                    return batch.output_file_id
                elif status.status == "failed":
                    raise RuntimeError("❌ バッチ失敗")
                time.sleep(60)

        except Exception as e:
            print(f"⚠️ Token limit reached or error occurred. Retry {attempt + 1}/{retries} in {wait} sec...")
            time.sleep(wait)
    raise RuntimeError("❌ リトライ上限に達しました")

# 入力データ設定
FILE_PATH = "/Users/kuramotomana/Test/20250602_最新年度.xlsx"
df = pd.read_excel(FILE_PATH)
df_filtered = df[df["対象疾患"].astype(str).str.contains("新生物", na=False)]
df_filtered = df_filtered.dropna(subset=["成果概要（日本語）"])

# トークン制限内のものだけ抽出
MAX_EMBED_TOKENS = 8192
examples_pool = []
for idx, row in df_filtered.iterrows():
    text = str(row["成果概要（日本語）"]).strip()
    ex_id = row["課題管理番号"]
    if count_tokens(text) <= MAX_EMBED_TOKENS:
        examples_pool.append((ex_id, text))

# 出力用ディレクトリ
os.makedirs("results_txt", exist_ok=True)
os.makedirs("results_csv", exist_ok=True)

# 1リクエスト分生成関数
def create_prompt_and_response():
    random.shuffle(examples_pool)

    MAX_INPUT_TOKENS = 125000
    MAX_OUTPUT_TOKENS = 2000

    example_text = ""
    total_tokens = 0
    examples_used = []

    for ex_id, ex_text in examples_pool:
        line = f"- {ex_text.strip()}\n"
        tokens = count_tokens(line)
        if total_tokens + tokens > MAX_INPUT_TOKENS:
            break
        example_text += line
        total_tokens += tokens
        examples_used.append((ex_id, ex_text.strip()))

    prompt = f"""
以下は研究成果概要の実例です。
これらを参考に、新たな架空の成果概要を1件だけ作成してください。

{example_text}
    """

    return prompt, examples_used

# バッチ実行ループ（10×10件）
for batch_num in range(1, 11):
    all_requests = []

    for request_num in range(1, 11):
        prompt, examples_used = create_prompt_and_response()

        all_requests.append({
            "custom_id": f"batch{batch_num:02}_req{request_num:02}",
            "method": "POST",
            "url": "/v1/chat/completions",
            "body": {
                "model": "gpt-4.1-mini",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 2000
            },
            "metadata": {
                "examples_used": examples_used
            }
        })

    # 送信・待機・出力取得
    output_file_id = send_batch_with_retry(all_requests)
    content = client.files.content(output_file_id).text.strip().split("\n")

    for line in content:
        res = json.loads(line)
        custom_id = res["custom_id"]
        response = res["response"]["body"]["choices"][0]["message"]["content"].strip()

        # 該当リクエストの参考例を取得
        examples_used = next(r["metadata"]["examples_used"] for r in all_requests if r["custom_id"] == custom_id)

        # 類似計算
        emb_generated = get_embedding(response)
        emb_examples = [get_embedding(text) for _, text in examples_used]
        similarities = cosine_similarity([emb_generated], emb_examples)[0]
        most_similar_index = int(np.argmax(similarities))
        most_similar_id, most_similar_text = examples_used[most_similar_index]
        similarity_score = similarities[most_similar_index]

        # 差分計算
        diff = list(difflib.ndiff(response.split(), most_similar_text.split()))
        diff_text = "\n".join(diff)

        # ファイル名と出力
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base = f"{timestamp}_{custom_id}_出力2000"

        with open(f"results_txt/{base}.txt", "w", encoding="utf-8") as f:
            f.write(response)

        with open(f"results_csv/{base}.csv", "w", encoding="utf-8") as f:
            f.write("生成された成果概要,類似成果概要,課題管理番号,類似度,差分\n")
            f.write(f"\"{response}\",\"{most_similar_text}\",{most_similar_id},{similarity_score:.4f},\"{diff_text}\"\n")

    print(f"✅ バッチ {batch_num}/10 完了")