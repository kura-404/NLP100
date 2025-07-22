# ========= オールインワン版スクリプト =========
import os
import sys
import pandas as pd
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed
from openai import OpenAI

# ========= 設定 =========
MODE = "test"  # "test" または "prod"

# テスト用
TEST_FILE = "/Users/kuramotomana/Test/LifeStory_2018_season1.xlsx"
TEST_COLUMN = "Sadness"
TEST_LIMIT = 100

# 本番用
INPUT_DIR = "excel_files"
OUTPUT_DIR = "output/csv"
MODEL = "gpt-4.1-mini"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# プロンプト
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

def classify_cells(cell_list):
    results = []
    for cell in tqdm(cell_list, desc="分類中", leave=False):
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
        results.append((cell, normalize_labels(label)))
    return results

def run_test_mode():
    df = pd.read_excel(TEST_FILE)
    if TEST_COLUMN not in df.columns:
        raise ValueError(f"列 {TEST_COLUMN} が存在しません")

    series = df[TEST_COLUMN].dropna().astype(str).iloc[:TEST_LIMIT]
    results = classify_cells(series.tolist())

    out_df = pd.DataFrame(results, columns=["セルの内容", "分類ラベル"])
    base = os.path.splitext(os.path.basename(TEST_FILE))[0]
    out_path = os.path.join(OUTPUT_DIR, f"{base}-{TEST_COLUMN}.csv")
    out_df.to_csv(out_path, index=False)
    print(f"✅ テスト出力完了: {out_path}")

def process_column(file, col):
    path = os.path.join(INPUT_DIR, file)
    df = pd.read_excel(path)
    if col not in df.columns:
        print(f"⚠️ 列 {col} が見つかりません: {file}")
        return
    series = df[col].dropna().astype(str)
    results = classify_cells(series.tolist())

    out_df = pd.DataFrame(results, columns=["セルの内容", "分類ラベル"])
    base = os.path.splitext(file)[0]
    safe_col = col.replace("/", "_").replace("\\", "_")
    out_path = os.path.join(OUTPUT_DIR, f"{base}-{safe_col}.csv")
    out_df.to_csv(out_path, index=False)
    print(f"✅ 出力完了: {out_path}")

def run_prod_mode():
    files = [f for f in os.listdir(INPUT_DIR) if f.endswith(".xlsx")]
    for file in tqdm(files, desc="📁 ファイル処理中"):
        df = pd.read_excel(os.path.join(INPUT_DIR, file))
        columns = df.columns.tolist()
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(process_column, file, col) for col in columns]
            for future in as_completed(futures):
                future.result()

if __name__ == "__main__":
    if MODE == "test":
        run_test_mode()
    elif MODE == "prod":
        run_prod_mode()
    else:
        raise ValueError("MODE must be 'test' または 'prod'")