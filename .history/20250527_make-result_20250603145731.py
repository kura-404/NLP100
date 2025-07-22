#成果概要（新生物）からランダムに125000トークン分を参考にして1件の架空の成果概要を生成する。加えて、参考にしたデータから一番似ているものとの類似度、差分を出力する。
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

# 設定
MAX_INPUT_TOKENS = 125000
MAX_OUTPUT_TOKENS = 2000
FILE_PATH = "/Users/kuramotomana/Test/20250602_最新年度.xlsx"

# 省略部分：OpenAIやトークン数カウントの初期設定などはこれまでと同じ

# データ読み込みとフィルター
df = pd.read_excel(FILE_PATH)
df_filtered = df[df["対象疾患"].astype(str).str.contains("新生物", na=False)]
df_filtered = df_filtered.dropna(subset=["成果概要（日本語）"])
examples_pool = df_filtered[["課題管理番号", "成果概要（日本語）"]].values.tolist()

# ランダムシャッフルと詰め込み
random.shuffle(examples_pool)
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

# 生成プロンプトとAPI呼び出しは同様

# 類似度計算
emb_generated = get_embedding(generated)
emb_examples = [get_embedding(text) for _, text in examples_used]
similarities = cosine_similarity([emb_generated], emb_examples)[0]
most_similar_index = int(np.argmax(similarities))
most_similar_id, most_similar_text = examples_used[most_similar_index]
similarity_score = similarities[most_similar_index]

# 差分と保存
with open(f"{base_filename}_比較結果.txt", "w", encoding="utf-8") as f:
    f.write("🧪 生成された成果概要\n")
    f.write(generated + "\n\n")
    f.write("🔍 最も類似した参考成果概要\n")
    f.write(f"課題管理番号: {most_similar_id}\n")
    f.write(most_similar_text + "\n\n")
    f.write(f"🔗 類似度スコア: {similarity_score:.4f}\n\n")
    f.write("🧬 差分（単語単位）\n")
    f.write("\n".join(difflib.ndiff(generated.split(), most_similar_text.split())))