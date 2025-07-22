# ========= オールインワン版スクリプト（進捗出力付き） =========
import os
import sys
import json
import time
import uuid
import pandas as pd
from tqdm import tqdm
from openai import OpenAI

# ========= 設定 =========
MODE = "test"  # "test" または "prod"

# テスト用
TEST_FILE = "Test/LifeStory_2018_season1.xlsx"
TEST_COLUMN = "Sadness"
TEST_LIMIT = 100

# 本番用
INPUT_DIR = "excel_files"
OUTPUT_DIR = "output/csv"
MODEL = "gpt-4.1-mini"
INTERVAL_SECONDS = 1
CHUNK_SIZE = 100

os.makedirs(OUTPUT_DIR, exist_ok=True)

SYSTEM_PROMPT = (
    "あなたはこれからテキスト分類に取り組んでください。以下の要件に従って、入力文を分類してください。\n\n"
    "【分類タスク】\n"
    "– ラベル: パートナー／家族／ペット／友人／同僚／それ以外の人物／AI／登場なし\n"
    "– 複数ラベルは空白区切りで記述（例：「家族 友人」）\n"
    "– ラベルがなければ「登場なし」と記述"
)

client = OpenAI()

def normalize_labels(label: str) -> str:
    return ",".join(label.replace("　", " ").replace(",", " ").split())

def classify_chunk(chunk: list[str]) -> list[str]:
    prompt = "\n".join(chunk)
    try:
        res = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ]
        )
        raw_output = res.choices[0].message.content.strip().split("\n")
        return [normalize_labels(label) for label in raw_output[:len(chunk)]]
    except Exception as e:
        return ["エラー"] * len(chunk)

def split_list(lst, n):
    return [lst[i:i + n] for i in range(0, len(lst), n)]

def process_file(filepath: str):
    df = pd.read_excel(filepath)
    file_id = os.path.splitext(os.path.basename(filepath))[0]

    print(f"📄 ファイル処理開始: {file_id}")

    for col in df.columns:
        series = df[col].dropna().astype(str)
        if series.empty:
            continue

        print(f"🔍 処理中の列: {col} ({len(series)}行)")
        chunks = split_list(series.tolist(), CHUNK_SIZE)
        results = []

        for i, chunk in enumerate(tqdm(chunks, desc=f"{file_id} - {col}")):
            print(f"  ▶️ チャンク {i + 1}/{len(chunks)} 件数: {len(chunk)}")
            labels = classify_chunk(chunk)
            results.extend(zip(chunk, labels))
            time.sleep(INTERVAL_SECONDS)

        df_out = pd.DataFrame(results, columns=["セルの内容", "分類ラベル"])
        output_path = os.path.join(OUTPUT_DIR, f"{file_id}-{col}.csv")
        df_out.to_csv(output_path, index=False, encoding="utf-8-sig")
        print(f"✅ 出力完了: {output_path}\n")

def run_test_mode():
    df = pd.read_excel(TEST_FILE)
    if TEST_COLUMN not in df.columns:
        raise ValueError(f"列 {TEST_COLUMN} が存在しません")

    series = df[TEST_COLUMN].dropna().astype(str).iloc[:TEST_LIMIT]
    chunks = split_list(series.tolist(), CHUNK_SIZE)
    results = []

    print(f"🧪 テスト列: {TEST_COLUMN} ({len(series)}行)")

    for i, chunk in enumerate(tqdm(chunks, desc="テスト分類")):
        print(f"  ▶️ チャンク {i + 1}/{len(chunks)} 件数: {len(chunk)}")
        labels = classify_chunk(chunk)
        results.extend(zip(chunk, labels))
        time.sleep(INTERVAL_SECONDS)

    df_out = pd.DataFrame(results, columns=["セルの内容", "分類ラベル"])
    name = os.path.splitext(os.path.basename(TEST_FILE))[0]
    path = os.path.join(OUTPUT_DIR, f"{name}-{TEST_COLUMN}.csv")
    df_out.to_csv(path, index=False, encoding="utf-8-sig")
    print(f"✅ テスト出力完了: {path}")

def run_prod_mode():
    files = [f for f in os.listdir(INPUT_DIR) if f.endswith(".xlsx")]
    for file in files:
        process_file(os.path.join(INPUT_DIR, file))

if __name__ == "__main__":
    if MODE == "test":
        run_test_mode()
    elif MODE == "prod":
        run_prod_mode()
    else:
        raise ValueError("MODE must be 'test' または 'prod'")
