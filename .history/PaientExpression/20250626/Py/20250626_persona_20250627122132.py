# 患者のペルソナを設定して、辞書の上位10件について患者表現を生成する
# コマンドライン引数で出力ファイル名に対してキーワードを設定できる
#
# 更新点：
# - OpenAIの「バッチAPI」を使用する形式に変更
# - バッチサイズを1リクエストに変更（デバッグ用）
# - AIへの指示からハイフンの縛りをなくし、よりシンプルに
# - 1データにつき必ず3つの出力列を生成するように修正

import csv
import json
import time
import os
import sys
import re
from datetime import datetime

import pandas as pd
from openai import OpenAI
from tqdm import tqdm
import tiktoken

# %% コマンドライン引数からキーワード取得
if len(sys.argv) < 2:
    print("❌ キーワードをコマンドライン引数で指定してください。")
    print("例: python your_script_name.py my_keyword")
    sys.exit(1)

keyword = sys.argv[1]

# %% OpenAIクライアント初期化
try:
    client = OpenAI()
except Exception as e:
    print("❌ OpenAIクライアントの初期化に失敗しました。APIキーが正しく設定されているか確認してください。")
    print(f"エラー詳細: {e}")
    sys.exit(1)


# %% ファイル読み込みとデータフィルタリング
# ★★★★★ ユーザーのローカル環境に合わせてファイルパスを更新 ★★★★★
FILE_NAME = "/Users/kuramotomana/Test/PaientExpression/20250626/Input/20250626_input.xlsx"

try:
    df = pd.read_excel(FILE_NAME)
except FileNotFoundError:
    print(f"❌ ファイルが見つかりません: {FILE_NAME}")
    sys.exit(1)
except Exception as e:
    print(f"❌ Excelファイルの読み込み中にエラーが発生しました: {e}")
    sys.exit(1)

# 欠損値・不正な正規形（-1, ERR）を持つ行を除外
    df_filtered = df[
        (df["出現形"].notna()) &
        (df["正規形"].notna()) &
        (~df["正規形"].astype(str).str.strip().isin(["-1", "ERR"]))
    ].reset_index(drop=True).copy()
# 欠損値・不正な正規形（-1, ERR）を持つ行を除外
# # 欠損値・不正な正規形（-1, ERR）を持つ行を除外
# df_filtered = df[
#     (df["出現形"].notna()) &
#     (df["正規形"].notna()) &
#     (~df["正規形"].astype(str).str.strip().isin(["-1", "ERR"]))
# ].head(1).reset_index(drop=True).copy() # ★★★ テスト用に最初の1件のみを対象にする ★★★
print(f"読み込みデータ: {len(df)}件, フィルタリング後の処理対象データ: {len(df_filtered)}件")


# %% 指示（プロンプト）の簡略化
INSTRUCTION = """# Instructions
あなたは病院の外来を受診した患者です。以下の「出現形」と「正規形」（医療用語）を参考に、医師に自分の症状を自然な言葉で3パターン伝えてください。

# ルール
- **必ず3つの異なる文章を、それぞれ改行で区切って作成してください。**
- 「どこが」「どんなとき」「どんなふうに」「どんなきっかけで」など、症状の場所、状況、感じ方も自由に加えてください。
- 自分の症状として、自然な話し言葉で伝えてください。
- 医療用語は使わないでください。
- 出現形・正規形に関連する症状のみに言及してください。
- 各文章の先頭にハイフンや番号などの記号は付けないでください。

# 出力形式の例
腕に小さいできものができて、押すとちょっと痛いです
最近、首の後ろにしこりみたいなものができて、気になっています
お腹にぷくっとした膨らみができて、だんだん大きくなっている気がします
"""

# %% OpenAI バッチAPIを使用した処理
output_records = []
# ★★★★★ ユーザーのローカル環境に合わせてバッチサイズを更新 ★★★★★
batch_size = 200

total_batches = -(-len(df_filtered) // batch_size) # 天井関数

for i in range(0, len(df_filtered), batch_size):
    batch_df = df_filtered.iloc[i:i + batch_size]
    current_batch_index = (i // batch_size) + 1
    
    print(f"\n--- Preparing Batch {current_batch_index} / {total_batches} ({len(batch_df)} records) ---")

    # 1. バッチAPI用の入力ファイル(JSONL形式)を作成
    batch_input_requests = []
    for index, row in batch_df.iterrows():
        custom_id = f"request-{row['行ID']}-{index}"
        messages = [
            {"role": "system", "content": f"あなたは{keyword}です。"},
            {"role": "user", "content": INSTRUCTION + f"\n\n# Input:\n出現形: {row['出現形']}\n正規形: {row['正規形']}"}
        ]
        batch_input_requests.append({
            "custom_id": custom_id,
            "method": "POST",
            "url": "/v1/chat/completions",
            "body": {
                "model": "gpt-4o-mini",
                "messages": messages,
                "max_tokens": 2000
            }
        })
    
    input_file_path = f"batch_input_{current_batch_index}.jsonl"
    with open(input_file_path, "w", encoding="utf-8") as f:
        for req in batch_input_requests:
            f.write(json.dumps(req) + "\n")

    # 2. 入力ファイルをOpenAIにアップロード
    print(f"Uploading batch file: {input_file_path}")
    with open(input_file_path, "rb") as f:
        batch_input_file = client.files.create(file=f, purpose="batch")
    
    # 3. バッチ処理を開始
    print(f"Creating batch job with file ID: {batch_input_file.id}")
    batch = client.batches.create(
        input_file_id=batch_input_file.id,
        endpoint="/v1/chat/completions",
        completion_window="24h"
    )
    print(f"Batch job created with ID: {batch.id}. Waiting for completion...")

    # 4. バッチ処理の完了を待機 (ポーリング)
    while batch.status not in ["completed", "failed", "cancelled"]:
        time.sleep(10)
        batch = client.batches.retrieve(batch.id)
        print(f"Current batch status: {batch.status} (Requests: {batch.request_counts.completed}/{batch.request_counts.total})")

    # 5. 結果を処理
    if batch.status == "completed":
        print("Batch job completed. Retrieving results...")
        result_file_id = batch.output_file_id
        result_content = client.files.content(result_file_id).read()
        
        results_map = {}
        for line in result_content.decode("utf-8").strip().split("\n"):
            # 空行があった場合にエラーにならないようにチェック
            if line:
                data = json.loads(line)
                results_map[data["custom_id"]] = data

        for index, row in batch_df.iterrows():
            custom_id = f"request-{row['行ID']}-{index}"
            result_data = results_map.get(custom_id)
            
            output_lines = []
            if result_data and result_data.get("response", {}).get("status_code") == 200:
                content = result_data["response"]["body"]["choices"][0]["message"]["content"].strip()
                output_lines = [line.strip("・- 「」\"").strip() for line in content.split('\n') if line.strip()]
            else:
                error_message = result_data.get("response", {}).get("body", {}).get("error", {}).get("message", "Unknown error")
                output_lines = [f"ERROR: {error_message}"] * 3

            # 必ず3つの要素を持つように出力を正規化
            final_outputs = output_lines[:3]
            while len(final_outputs) < 3:
                final_outputs.append("")

            output_records.append([
                row["行ID"], row["ID"], row["出現形"], row["正規形"],
                row.get("TREE", ""), row.get("正規形_flag", "")
            ] + final_outputs)
            
    else:
        print(f"❌ Batch job failed or was cancelled. Status: {batch.status}")
        for index, row in batch_df.iterrows():
            output_records.append([
                row["行ID"], row["ID"], row["出現形"], row["正規形"],
                row.get("TREE", ""), row.get("正規形_flag", "")
            ] + [f"ERROR: Batch failed with status {batch.status}"] * 3)

    # 6. 一時ファイルを削除
    os.remove(input_file_path)
    print(f"Cleaned up temporary file: {input_file_path}")


# %% CSV出力 (全バッチ処理完了後)
timestamp = datetime.now().strftime("%Y%m%d_%H%M")
output_filename = f"{timestamp}_{keyword}_患者表現.csv"

columns = ["行ID", "ID", "出現形", "正規形", "TREE", "正規形_flag", "出力1", "出力2", "出力3"]

df_output = pd.DataFrame(output_records, columns=columns)
df_output.to_csv(output_filename, index=False, encoding='utf-8-sig')

print(f"\n✅ 全ての処理が完了しました。出力結果を {output_filename} に保存しました。")
