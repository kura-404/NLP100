#患者のペルソナを設定して、辞書の上位10件について患者表現を生成する（バッチ処理じゃない）
import csv
import json
import time
import os
from datetime import datetime
import re

import pandas as pd
from openai import OpenAI
from tqdm import tqdm
import tiktoken

#%% OpenAIクライアント初期化
client = OpenAI()

#%% トークンカウント準備（cl100k_base = gpt-4.1-mini相当）
encoding = tiktoken.get_encoding("cl100k_base")

def count_tokens(text):
    return len(encoding.encode(text))

#%% 出力を番号付きで分割する関数
def split_numbered_responses(text):
    parts = re.split(r'\s*\d+\.\s*', text.strip())
    return [part for part in parts if part]

#%% ファイル読み込みとデータフィルタリング
FILE_NAME = "/Users/kuramotomana/Test/20250623_Only-R.csv"
df = pd.read_csv(FILE_NAME)

# タイトル行を除く → 欠損・不正な正規形（-1, ERR）を除く
df = df.iloc[1:]
df_filtered = df[
    (df["出現形"].notna()) &
    (df["正規形"].notna()) &
    (~df["正規形"].astype(str).str.strip().isin(["-1", "ERR"]))
].head(10).reset_index(drop=True).copy() # データを10件に制限

# 指示文
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

#%% 逐次処理と結果の格納
output_records = []

# tqdmを使って進捗を表示
for i, row in tqdm(df_filtered.iterrows(), total=len(df_filtered), desc="Processing requests"):
    messages = [
        {"role": "system", "content": "あなたは日本の子どもです。"},
        {"role": "user", "content": INSTRUCTION + f"\n\n# Input:\n出現形: {row['出現形']}\n正規形: {row['正規形']}"}
    ]

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini", # モデル名をgpt-4o-miniに変更しました。gpt-4.1-miniは存在しないモデル名のため。
            messages=messages,
            max_tokens=2000
        )
        content = response.choices[0].message.content.strip()

        output_lines = [line.strip("・- 「」\"").strip() for line in content.split('\n') if line.strip().startswith(("-", "・"))]
        if not output_lines:
            output_lines = split_numbered_responses(content.strip())
            output_lines = [line.strip("・- 「」\"").strip() for line in output_lines if line.strip()]

        output_records.append([
            row["行ID"],
            row["ID"],
            row["出現形"],
            row["正規形"]
        ] + output_lines)
        time.sleep(0.5) # APIレート制限を考慮して少し待機

    except Exception as e:
        print(f"Error processing request for row {i}: {e}")
        # エラー発生時も元の情報を記録し、出力部分は空にする
        output_records.append([
            row["行ID"],
            row["ID"],
            row["出現形"],
            row["正規形"]
        ] + [""] * 3) # 例えば3パターンを期待しているなら、空文字列を3つ追加
        time.sleep(1) # エラー時は少し長めに待機


#%% CSV出力
timestamp = datetime.now().strftime("%Y%m%d_%H%M")
output_filename = f"{timestamp}_症状出力結果.csv"

# output_recordsが空でないことを確認してから最大出力数を計算
if output_records:
    max_outputs = max(len(record) for record in output_records) - 4
else:
    max_outputs = 0 # output_recordsが空の場合は0にする

columns = ["行ID", "ID", "出現形", "正規形"] + [f"出力{i+1}" for i in range(max_outputs)]

df_output = pd.DataFrame(output_records, columns=columns)
df_output.to_csv(output_filename, index=False, encoding='utf-8-sig')

print(f"✅ 出力結果を {output_filename} に保存しました。")
