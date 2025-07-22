# ========= config.py =========
import os

# モード: "test" または "prod"
MODE = "test"

# テスト用設定
TEST_FILE = "Test/LifeStory_2018_season1.xlsx"
TEST_COLUMN = "Sadness"
TEST_LIMIT = 100  # 最大リクエスト数（テスト用）

# 本番用設定
INPUT_DIR = "excel_files"
BATCH_OUTPUT_DIR = "output/jsonl"

# 出力設定
os.makedirs(BATCH_OUTPUT_DIR, exist_ok=True)

# OpenAIモデル
MODEL = "gpt-4.1-mini"

# システムプロンプト
SYSTEM_PROMPT = (
    "あなたはこれからテキスト分類に取り組んでください。以下の要件に従って、入力文を分類してください。\n\n"
    "【分類タスク】\n"
    "– ラベル: パートナー／家族/ペット/友人/同僚/それ以外の人物/登場なし\n"
    "– 複数ラベルは空白区切りで記述（例：「家族 友人」）\n"
    "– ラベルがなければ「登場なし」と記述"
)

# ========= test_mode.py =========
import pandas as pd
from openai import OpenAI
from tqdm import tqdm
from config import TEST_FILE, TEST_COLUMN, TEST_LIMIT, SYSTEM_PROMPT, MODEL

client = OpenAI()

def run_test_mode():
    df = pd.read_excel(TEST_FILE)
    if TEST_COLUMN not in df.columns:
        raise ValueError(f"列 {TEST_COLUMN} が存在しません")

    series = df[TEST_COLUMN].dropna().astype(str).iloc[:TEST_LIMIT]
    print(f"▶️ テストモード実行: {len(series)}セル (最大{TEST_LIMIT}件)")

    results = []
    for cell in tqdm(series, desc="分類中"):
        try:
            res = client.chat.completions.create(
                model=MODEL,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": cell}
                ]
            )
            label = res.choices[0].message.content.strip()
        except Exception as e:
            label = "エラー"
            print(f"❌ エラー: {e}")
        results.append(label)

    out = pd.DataFrame({"元の値": series.tolist(), "分類ラベル": results})
    out.to_excel("output/test_result.xlsx", index=False)
    print("✅ テスト出力完了 → output/test_result.xlsx")

# ========= batch_builder.py =========
import os
import json
import pandas as pd
from tqdm import tqdm
import tiktoken
from config import INPUT_DIR, BATCH_OUTPUT_DIR, SYSTEM_PROMPT, MODEL

encoding = tiktoken.encoding_for_model(MODEL)


def estimate_tokens(text):
    return len(encoding.encode(text))

def build_batches():
    files = [f for f in os.listdir(INPUT_DIR) if f.endswith(".xlsx")]
    batch_id = 0

    for file in files:
        path = os.path.join(INPUT_DIR, file)
        df = pd.read_excel(path)
        records = []

        for col in df.columns:
            for cell in df[col].dropna().astype(str):
                user_content = cell.strip()
                tokens = estimate_tokens(SYSTEM_PROMPT) + estimate_tokens(user_content)

                records.append({
                    "messages": [
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": user_content}
                    ],
                    "tokens": tokens
                })

        total_tokens = sum(r["tokens"] for r in records)
        print(f"📦 {file}: {len(records)}リクエスト / 推定 {total_tokens}トークン")

        batch_path = os.path.join(BATCH_OUTPUT_DIR, f"batch_{batch_id}.jsonl")
        with open(batch_path, "w", encoding="utf-8") as f:
            for r in records:
                json.dump({"messages": r["messages"]}, f, ensure_ascii=False)
                f.write("\n")

        batch_id += 1

# ========= submit_batch.py =========
import os
from openai import OpenAI
from config import BATCH_OUTPUT_DIR, MODEL

client = OpenAI()

def submit_batches():
    files = sorted(f for f in os.listdir(BATCH_OUTPUT_DIR) if f.endswith(".jsonl"))
    for f in files:
        path = os.path.join(BATCH_OUTPUT_DIR, f)
        print(f"🚀 送信: {f}")
        with open(path, "rb") as batch_file:
            resp = client.batches.create(
                input_file=batch_file,
                endpoint="/v1/chat/completions",
                completion_window="24h",
                model=MODEL
            )
            print(f"🆔 Batch ID: {resp.id}")

# ========= main.py =========
from config import MODE
from test_mode import run_test_mode
from batch_builder import build_batches
from submit_batch import submit_batches

if MODE == "test":
    run_test_mode()
elif MODE == "prod":
    build_batches()
    submit_batches()
else:
    raise ValueError("MODE must be 'test' or 'prod'")