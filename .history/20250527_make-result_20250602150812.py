#成果概要（新生物）からランダムに125000トークン分を参考にして1件の架空の成果概要を
import pandas as pd
import tiktoken
import json
import random
import time
from openai import OpenAI
from datetime import datetime

# OpenAIクライアント初期化
client = OpenAI()

# トークンエンコーダ
encoding = tiktoken.get_encoding("cl100k_base")
def count_tokens(text: str) -> int:
    return len(encoding.encode(text))

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
for ex in examples_pool:
    line = f"- {ex.strip()}\n"
    tokens = count_tokens(line)
    if total_tokens + tokens > MAX_INPUT_TOKENS:
        break
    example_text += line
    total_tokens += tokens
    used_count += 1

# プロンプト作成
prompt = f"""
以下は研究成果概要の実例です。
これらを参考に、新たな架空の成果概要を1件だけ作成してください。

{example_text}
"""

# OpenAI APIリクエスト
response = client.chat.completions.create(
    model="gpt-4.1-mini",
    messages=[
        {"role": "user", "content": prompt}
    ],
    max_tokens=MAX_OUTPUT_TOKENS
)

# 出力取得
result = response.choices[0].message.content.strip()

# 出力保存（TXT形式、本文のみ）
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
output_filename = f"{timestamp}_出力2000_参考{used_count}件_batchTEST.txt"
with open(output_filename, "w", encoding="utf-8") as f:
    f.write(result)

print(f"✅ テストバッチ完了 → {output_filename}")