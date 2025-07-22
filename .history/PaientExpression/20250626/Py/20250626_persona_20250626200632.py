# 患者のペルソナを設定して、辞書の上位10件について患者表現を生成する
# コマンドライン引数で出力ファイル名に対してキーワードを設定できる
#
# 更新点：
# - 100件ずつの固定バッチ処理に戻す
# - 入力ファイルとしてExcel形式 (.xlsx) を使用
# - 出力に「正規形_flag」列を追加

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


# %% トークンカウント準備（cl100k_base = gpt-4o-mini相当）
encoding = tiktoken.get_encoding("cl100k_base")

def count_tokens(text):
    """テキストのトークン数を数える関数"""
    return len(encoding.encode(text))

# %% 出力を番号付きで分割する関数
def split_numbered_responses(text):
    """番号付きの応答テキストをリストに分割する関数"""
    parts = re.split(r'\s*\d+\.\s*', text.strip())
    return [part for part in parts if part]

# %% ファイル読み込みとデータフィルタリング
FILE_NAME = "/Users/kuramotomana/Test/PaientExpression/20250626/Input/20250626_input.xlsx" # ここにご自身のExcelファイルパスを指定してください

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

# Examples
Input:
出現形: できものができている
正規形: 皮下腫瘤

Output:
- 「腕に小さいできものができて、押すとちょっと痛いです」
- 「首の後ろにしこりみたいなものができて、不安です」
"""

# %% ★★★★★ 変更点: 100リクエスト（行）ずつの固定バッチ処理 ★★★★★
output_records = []
batch_size = 100 # 1バッチあたりのリクエスト数を100に設定

# 総バッチ数を計算 (例: 250件なら3バッチ)
total_batches = -(-len(df_filtered) // batch_size) # 天井関数

# batch_sizeごとにループ処理
for i in range(0, len(df_filtered), batch_size):
    # 現在のバッチのデータフレームをスライスで取得
    batch_df = df_filtered.iloc[i:i + batch_size]
    
    current_batch_index = (i // batch_size) + 1
    print(f"\n--- Processing Batch {current_batch_index} / {total_batches} ({len(batch_df)} records) ---")

    # tqdmを使ってバッチごとの進捗を表示
    for _, row in tqdm(batch_df.iterrows(), total=len(batch_df), desc=f"Batch {current_batch_index}"):
        messages = [
            {"role": "system", "content": f"あなたは日本の{keyword}です。"},
            {"role": "user", "content": INSTRUCTION + f"\n\n# Input:\n出現形: {row['出現形']}\n正規形: {row['正規形']}"}
        ]

        try:
            response = client.chat.completions.create(
                model="gpt-4.1-mini",
                messages=messages,
                max_tokens=2000,
                temperature=0.7
            )
            content = response.choices[0].message.content.strip()

            # 生成されたテキストを行ごとに分割し、不要な文字を除去
            output_lines = [line.strip("・- 「」\"").strip() for line in content.split('\n') if line.strip().startswith(("-", "・"))]
            
            # 上記でうまく分割できなかった場合、番号付きリストとして分割を試みる
            if not output_lines:
                output_lines = split_numbered_responses(content)
                output_lines = [line.strip("・- 「」\"").strip() for line in output_lines if line.strip()]

            # 結果をリストに追加
            output_records.append([
                row["行ID"],
                row["ID"],
                row["出現形"],
                row["正規形"],
                row.get("TREE", ""),  # .get()を使い、列が存在しなくてもエラーにならないようにする
                row.get("正規形_flag", "") # .get()で安全に値を取得
            ] + output_lines)
            
            time.sleep(0.5)  # APIのレート制限を考慮して0.5秒待機

        except Exception as e:
            print(f"\nError processing request for row ID {row.get('行ID', 'N/A')}: {e}")
            # エラーが発生した場合も、元のデータとエラーメッセージを記録する
            output_records.append([
                row["行ID"],
                row["ID"],
                row["出現形"],
                row["正規形"],
                row.get("TREE", ""),
                row.get("正規形_flag", "")
            ] + [f"ERROR: {e}"] * 3)
            time.sleep(1)


# %% CSV出力 (全バッチ処理完了後)
timestamp = datetime.now().strftime("%Y%m%d_%H%M")
output_filename = f"{timestamp}_{keyword}_患者表現.csv"

# output_recordsが空でないことを確認してから最大出力数を計算
if output_records:
    # ヘッダーの基本列数 (行ID, ID, 出現形, 正規形, TREE, 正規形_flag)
    max_outputs = max(len(record) for record in output_records) - 6
else:
    max_outputs = 0

# 出力用のカラムリストを定義
columns = ["行ID", "ID", "出現形", "正規形", "TREE", "正規形_flag"] + [f"出力{i+1}" for i in range(max_outputs)]

# DataFrameを作成し、CSVとして出力
df_output = pd.DataFrame(output_records)
# 可変長のリストからDataFrameを作成したため、列名を明示的に設定
df_output.columns = columns[:len(df_output.columns)] 
df_output.to_csv(output_filename, index=False, encoding='utf-8-sig')

print(f"\n✅ 全ての処理が完了しました。出力結果を {output_filename} に保存しました。")
