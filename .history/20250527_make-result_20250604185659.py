import subprocess
import sys

# 必要なパッケージのインストール確認
def ensure_package_installed(package):
    try:
        __import__(package)
    except ImportError:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])

# 必要パッケージを確認
for pkg in ["tiktoken", "pandas", "openai", "scikit-learn"]:
    ensure_package_installed(pkg)

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

# OpenAIクライアント初期化
client = OpenAI()

# トークンエンコーダ
encoding = tiktoken.get_encoding("cl100k_base")
def count_tokens(text: str) -> int:
    return len(encoding.encode(text))

# 埋め込み取得
def get_embedding(text: str) -> list:
    response = client.embeddings.create(
        input=[text],
        model="text-embedding-3-small"
    )
    return response.data[0].embedding

# 各リクエスト処理
def run_request(batch_num: int, request_num: int, examples_pool):
    # シャッフルと初期化
    random.shuffle(examples_pool)
    example_text = ""
    total_tokens = 0
    used_count = 0
    examples_used = []

    for ex_id, ex_text in examples_pool:
        line = f"- {ex_text.strip()}\n"
        tokens = count_tokens(line)
        if total_tokens + tokens > 125000:
            break
        example_text += line
        total_tokens += tokens
        used_count += 1
        examples_used.append((ex_id, ex_text.strip()))

    # プロンプト作成
    prompt = f"""
以下は研究成果概要の実例です。
これらを参考に、新たな架空の成果概要を1件だけ作成してください。

{example_text}
"""

    # 生成
    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=2000
    )
    generated = response.choices[0].message.content.strip()

    # 類似度計算
    emb_generated = get_embedding(generated)
    emb_examples = [get_embedding(text) for _, text in examples_used]
    similarities = cosine_similarity([emb_generated], emb_examples)[0]
    most_similar_index = int(np.argmax(similarities))
    most_similar_id, most_similar_text = examples_used[most_similar_index]
    similarity_score = similarities[most_similar_index]

    # 差分抽出
    diff = list(difflib.ndiff(generated.split(), most_similar_text.split()))
    diff_text = "\n".join(diff)

    # 保存
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    base_filename = f"{timestamp}_batch{batch_num}_req{request_num}_出力2000_参考{used_count}件"

    with open(f"{base_filename}.txt", "w", encoding="utf-8") as f:
        f.write(generated)

    with open(f"{base_filename}_比較結果.txt", "w", encoding="utf-8") as f:
        f.write("🧪 生成された成果概要\n")
        f.write(generated + "\n\n")
        f.write("🔍 最も類似した参考成果概要\n")
        f.write(f"課題管理番号: {most_similar_id}\n")
        f.write(most_similar_text + "\n\n")
        f.write(f"🔗 類似度スコア: {similarity_score:.4f}\n\n")
        f.write("🧬 差分（単語単位）\n")
        f.write(diff_text)

    print(f"✅ batch {batch_num} / request {request_num} 完了")

# バッチ実行関数
def run_batches():
    FILE_PATH = "/Users/kuramotomana/Test/20250602_最新年度.xlsx"
    df = pd.read_excel(FILE_PATH)
    df_filtered = df[df["対象疾患"].astype(str).str.contains("新生物", na=False)]
    df_filtered = df_filtered.dropna(subset=["成果概要（日本語）"])
    examples_pool = df_filtered[["課題管理番号", "成果概要（日本語）"]].values.tolist()

    for batch_num in range(1, 11):
        for request_num in range(1, 11):
            run_request(batch_num, request_num, examples_pool)
            time.sleep(1)  # API制限対策（必要に応じて調整）

# 実行
if __name__ == "__main__":
    run_batches()