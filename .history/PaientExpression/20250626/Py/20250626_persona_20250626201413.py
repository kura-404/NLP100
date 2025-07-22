# 患者のペルソナを設定して、辞書の上位10件について患者表現を生成する
# コマンドライン引数で出力ファイル名に対してキーワードを設定できる
#
# 更新点：
# - OpenAIの「バッチAPI」を使用する形式に変更
# - 100リクエストを1つのバッチファイルとして投入
# - 入力ファイルとしてExcel形式 (.xlsx) を使用
# - 出力に「正規形_flag」列を追加
# - systemプロンプトにコマンドライン引数のキーワードを使用

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


# %% 出力を番号付きで分割する関数
def split_numbered_responses(text):
    """番号付きの応答テキストをリストに分割する関数"""
    parts = re.split(r'\s*\d+\.\s*', text.strip())
    return [part for part in parts if part]

# %% ファイル読み込みとデータフィルタリング
FILE_NAME = "/Users/kuramotomana/Test/your_input_file.xlsx" # ここにご自身のExcelファイルパスを指定してください

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

print(f"読み込みデータ: {len(df)}件, フィルタリング後の処理対象データ: {len(df_filtered)}件")


# %% 指示文（プロンプト）
INSTRUCTION = """# Instructions
あなたは病院の外来を受診した患者です。以下の「出現形」と「正規形」（医療用語）を参考に、医師に自分の症状を自然な言葉で伝えてください。
- 「どこが」「どんなとき」「どんなふうに」「どんなきっかけで」など、症状の場所、状況、感じ方も自由に加えてください。
- 誰かの話ではなく、自分の症状として話してください。
- 医療用語は使わず、家族や友人に話すような言い回しにしてください。
- ３パターン作成してください。
- **出現形・正規形に関連する症状のみに言及し、それ以外の症状（例：他の部位の痛み・他の体調変化など）には触れないでください。**
"""

# %% ★★★★★ OpenAI バッチAPIを使用した処理 ★★★★★
output_records = []
batch_size = 100 # 1バッチあたりのリクエスト数を100に設定

total_batches = -(-len(df_filtered) // batch_size) # 天井関数

for i in range(0, len(df_filtered), batch_size):
    batch_df = df_filtered.iloc[i:i + batch_size]
    current_batch_index = (i // batch_size) + 1
    
    print(f"\n--- Preparing Batch {current_batch_index} / {total_batches} ({len(batch_df)} records) ---")

    # 1. バッチAPI用の入力ファイル(JSONL形式)を作成
    batch_input_requests = []
    for index, row in batch_df.iterrows():
        # 結果を紐付けるためのユニークID
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
                "max_tokens": 2000,
                "temperature": 0.7
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
        completion_window="24h" # 24時間以内に処理を完了させる
    )
    print(f"Batch job created with ID: {batch.id}. Waiting for completion...")

    # 4. バッチ処理の完了を待機 (ポーリング)
    while batch.status not in ["completed", "failed", "cancelled"]:
        time.sleep(10) # 10秒ごとにステータスを確認
        batch = client.batches.retrieve(batch.id)
        print(f"Current batch status: {batch.status} (Requests: {batch.request_counts.completed}/{batch.request_counts.total})")

    # 5. 結果を処理
    if batch.status == "completed":
        print("Batch job completed. Retrieving results...")
        # 結果ファイルの内容を取得
        result_file_id = batch.output_file_id
        result_content = client.files.content(result_file_id).read()
        
        # 結果を custom_id をキーにした辞書に格納
        results_map = {}
        for line in result_content.decode("utf-8").strip().split("\n"):
            data = json.loads(line)
            results_map[data["custom_id"]] = data

        # 元のデータと結果を紐付けて整形
        for index, row in batch_df.iterrows():
            custom_id = f"request-{row['行ID']}-{index}"
            result_data = results_map.get(custom_id)
            
            output_lines = []
            if result_data and result_data.get("response", {}).get("status_code") == 200:
                content = result_data["response"]["body"]["choices"][0]["message"]["content"].strip()
                output_lines = [line.strip("・- 「」\"").strip() for line in content.split('\n') if line.strip().startswith(("-", "・"))]
                if not output_lines:
                    output_lines = split_numbered_responses(content)
                    output_lines = [line.strip("・- 「」\"").strip() for line in output_lines if line.strip()]
            else:
                error_message = result_data.get("response", {}).get("body", {}).get("error", {}).get("message", "Unknown error")
                output_lines = [f"ERROR: {error_message}"] * 3

            output_records.append([
                row["行ID"], row["ID"], row["出現形"], row["正規形"],
                row.get("TREE", ""), row.get("正規形_flag", "")
            ] + output_lines)
            
    else:
        print(f"❌ Batch job failed or was cancelled. Status: {batch.status}")
        # バッチが失敗した場合も、元のデータをエラーとして記録
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

if output_records:
    max_outputs = max(len(record) for record in output_records) - 6
else:
    max_outputs = 0

columns = ["行ID", "ID", "出現形", "正規形", "TREE", "正規形_flag"] + [f"出力{i+1}" for i in range(max_outputs)]

df_output = pd.DataFrame(output_records)
df_output.columns = columns[:len(df_output.columns)] 
df_output.to_csv(output_filename, index=False, encoding='utf-8-sig')

print(f"\n✅ 全ての処理が完了しました。出力結果を {output_filename} に保存しました。")
