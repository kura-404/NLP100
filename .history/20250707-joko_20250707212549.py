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
BATCH_OUTPUT_DIR = "output/csv"

# 出力設定
os.makedirs(BATCH_OUTPUT_DIR, exist_ok=True)


# OpenAIモデル
MODEL = "gpt-4.1-mini"

# システムプロンプト
SYSTEM_PROMPT = (
    "あなたはこれからテキスト分類に取り組んでください。以下の要件に従って、入力文を分類してください。\n\n"
    "【分類タスク】\n"
    "– ラベル: パートナー／家族／ペット／友人／同僚／それ以外の人物／AI／登場なし\n"
    "– 複数ラベルは空白区切りで記述（例：「家族 友人」）\n"
    "– ラベルがなければ「登場なし」と記述"
)

# ========= test_mode.py =========
import pandas as pd
from openai import OpenAI
from tqdm import tqdm
from config import TEST_FILE, TEST_COLUMN, TEST_LIMIT, SYSTEM_PROMPT, MODEL, BATCH_OUTPUT_DIR
import os

client = OpenAI()

def normalize_labels(label: str) -> str:
    return ",".join(label.replace("　", " ").replace(",", " ").split())

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
        results.append((cell, normalize_labels(label)))

    out_df = pd.DataFrame(results, columns=["セルの内容", "分類ラベル"])
    filename = os.path.splitext(os.path.basename(TEST_FILE))[0]
    out_df.to_csv(os.path.join(BATCH_OUTPUT_DIR, f"{filename}-{TEST_COLUMN}.csv"), index=False)
    print(f"✅ 出力完了 → {filename}-{TEST_COLUMN}.csv")

# ========= batch_builder.py =========
import os
import pandas as pd
from tqdm import tqdm
from openai import OpenAI
from concurrent.futures import ThreadPoolExecutor, as_completed
from config import INPUT_DIR, BATCH_OUTPUT_DIR, SYSTEM_PROMPT, MODEL

client = OpenAI()

def normalize_labels(label: str) -> str:
    return ",".join(label.replace("　", " ").replace(",", " ").split())

def process_column(file, col):
    path = os.path.join(INPUT_DIR, file)
    df = pd.read_excel(path)
    if col not in df.columns:
        print(f"⚠️ 列 {col} が見つかりません: {file}")
        return

    series = df[col].dropna().astype(str)
    results = []

    for cell in tqdm(series, desc=f"{file} - {col}", leave=False):
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

    out_df = pd.DataFrame(results, columns=["セルの内容", "分類ラベル"])
    base = os.path.splitext(file)[0]
    safe_col = col.replace("/", "_").replace("\\", "_")
    out_path = os.path.join(BATCH_OUTPUT_DIR, f"{base}-{safe_col}.csv")
    out_df.to_csv(out_path, index=False)
    print(f"✅ 出力完了: {out_path}")

def build_batches():
    files = [f for f in os.listdir(INPUT_DIR) if f.endswith(".xlsx")]

    for file in tqdm(files, desc="📁 ファイル処理中"):
        path = os.path.join(INPUT_DIR, file)
        df = pd.read_excel(path)
        columns = df.columns.tolist()

        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(process_column, file, col) for col in columns]
            for future in as_completed(futures):
                future.result()

# ========= main.py =========
from config import MODE
from test_mode import run_test_mode
from batch_builder import build_batches

if MODE == "test":
    run_test_mode()
elif MODE == "prod":
    build_batches()
else:
    raise ValueError("MODE must be 'test' or 'prod'")