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
FILE_PATH = "/Users/kuramotomana/Test/20250527-merged_output.csv"

# データ読み込み
df = pd.read_csv(FILE_PATH)
df_filtered = df[df["対象疾患"].astype(str).str.contains("新生物", na=False)]
examples_pool = df_filtered["成果概要（日本語）"].dropna().astype(str).tolist()

# ランダムシャッフル
random.shuffle(examples_pool)

# 成果概要を詰め込む
example_text = ""
total_tokens = 0
used_count = 0
examples_used = []

for ex in examples_pool:
    line = f"- {ex.strip()}\n"
    tokens = count_tokens(line)
    if total_tokens + tokens > MAX_INPUT_TOKENS:
        break
    example_text += line
    total_tokens += tokens
    used_count += 1
    examples_used.append(ex.strip())

# プロンプト作成
prompt = f"""
以下は研究成果概要の実例です。
これらを参考に、新たな架空の成果概要を1件だけ作成してください。

{example_text}
"""

# OpenAI APIリクエスト（生成）
response = client.chat.completions.create(
    model="gpt-4.1-mini",
    messages=[{"role": "user", "content": prompt}],
    max_tokens=MAX_OUTPUT_TOKENS
)
generated = response.choices[0].message.content.strip()

# 類似度計算
emb_generated = get_embedding(generated)
emb_examples = [get_embedding(text) for text in examples_used]
similarities = cosine_similarity([emb_generated], emb_examples)[0]
most_similar_index = int(np.argmax(similarities))
most_similar_text = examples_used[most_similar_index]
similarity_score = similarities[most_similar_index]

# 差分抽出
diff = list(difflib.ndiff(generated.split(), most_similar_text.split()))
diff_text = "\n".join(diff)

# 保存
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
base_filename = f"{timestamp}_出力2000_参考{used_count}件_batchTEST"

# 出力テキスト保存（本文のみ）
with open(f"{base_filename}.txt", "w", encoding="utf-8") as f:
    f.write(generated)

# 類似結果と差分保存
with open(f"{base_filename}_比較結果.txt", "w", encoding="utf-8") as f:
    f.write("🧪 生成された成果概要\n")
    f.write(generated + "\n\n")
    f.write("🔍 最も類似した参考成果概要\n")
    f.write(most_similar_text + "\n\n")
    f.write(f"🔗 類似度スコア: {similarity_score:.4f}\n\n")
    f.write("🧬 差分（単語単位）\n")
    f.write(diff_text)

# 完了
print(f"✅ 出力を保存しました：\n- {base_filename}.txt\n- {base_filename}_比較結果.txt")