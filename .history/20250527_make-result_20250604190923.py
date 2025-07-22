# 成果概要（新生物）からランダムに125000トークン分を参考にして1件の架空の成果概要を生成する。
# 加えて、参考にしたデータから一番似ているものとの類似度、差分、課題管理番号を出力する（8192トークン超過は除外）。

import pandas as pd
import tiktoken
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

# パラメータ設定
MAX_INPUT_TOKENS = 125000
MAX_OUTPUT_TOKENS = 2000
MAX_EMBED_TOKENS = 8192
FILE_PATH = "/Users/kuramotomana/Test/20250602_最新年度.xlsx"

# データ読み込み
df = pd.read_excel(FILE_PATH)
df_filtered = df[df["対象疾患"].astype(str).str.contains("新生物", na=False)]
df_filtered = df_filtered.dropna(subset=["成果概要（日本語）"])

# トークン制限内のものだけを抽出
examples_pool = []
for idx, row in df_filtered.iterrows():
    text = str(row["成果概要（日本語）"]).strip()
    ex_id = row["課題管理番号"]
    if count_tokens(text) <= MAX_EMBED_TOKENS:
        examples_pool.append((ex_id, text))

# 実行関数（1リクエスト分）
def run_request(batch_num, request_num, examples_pool):
    random.shuffle(examples_pool)

    # 成果概要詰め込み
    example_text = ""
    total_tokens = 0
    used_count = 0
    examples_used = []

    for ex_id, ex_text in examples_pool:
        line = f"- {ex_text}\n"
        tokens = count_tokens(line)
        if total_tokens + tokens > MAX_INPUT_TOKENS:
            break
        example_text += line
        total_tokens += tokens
        used_count += 1
        examples_used.append((ex_id, ex_text))

    # プロンプト
    prompt = f"""
以下は研究成果概要の実例です。
これらを参考に、新たな架空の成果概要を1件だけ作成してください。

{example_text}
    """

    # 生成
    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=MAX_OUTPUT_TOKENS
    )
    generated = response.choices[0].message.content.strip()

    # 類似度比較
    emb_generated = get_embedding(generated)
    emb_examples = [get_embedding(text) for _, text in examples_used]
    similarities = cosine_similarity([emb_generated], emb_examples)[0]
    most_similar_index = int(np.argmax(similarities))
    most_similar_id, most_similar_text = examples_used[most_similar_index]
    similarity_score = similarities[most_similar_index]

    # 差分
    diff = list(difflib.ndiff(generated.split(), most_similar_text.split()))
    diff_text = "\n".join(diff)

    # 保存
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    base_filename = f"{timestamp}_batch{batch_num:02}_req{request_num:02}_出力2000_参考{used_count}件"

    os.makedirs("outputs", exist_ok=True)
    with open(f"outputs/{base_filename}.txt", "w", encoding="utf-8") as f:
        f.write(generated)

    with open(f"outputs/{base_filename}_比較結果.txt", "w", encoding="utf-8") as f:
        f.write("🧪 生成された成果概要\n")
        f.write(generated + "\n\n")
        f.write("🔍 最も類似した参考成果概要\n")
        f.write(f"課題管理番号: {most_similar_id}\n")
        f.write(most_similar_text + "\n\n")
        f.write(f"🔗 類似度スコア: {similarity_score:.4f}\n\n")
        f.write("🧬 差分（単語単位）\n")
        f.write(diff_text)

    print(f"✅ batch {batch_num} / request {request_num} 完了")

# 全体バッチループ（10×10回）
def run_batches():
    for batch_num in range(1, 11):
        for request_num in range(1, 11):
            run_request(batch_num, request_num, examples_pool)
            time.sleep(1)

# 実行
if __name__ == "__main__":
    run_batches()