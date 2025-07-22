# -*- coding: utf-8 -*-
import pandas as pd
import csv
from datetime import datetime
from openai import OpenAI
from dotenv import load_dotenv

# .envからAPIキー読み込み
load_dotenv()

# OpenAIクライアント初期化
client = OpenAI()

# 入力CSVファイルと対象列名
input_file = "/Users/kuramotomana/Test/combined.csv"
target_column = "生成された成果概要"  # 書き換え対象の列名
output_column = "書き換え後：成果概要"

# 出力ファイル名（タイムスタンプ付き）
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
output_file = f"rewritten_output_{timestamp}.csv"

# CSV読み込み
df = pd.read_csv(input_file)

# 新しい列を作成し、書き換え結果を格納
rewritten_list = []

SYSTEM_PROMPT = """
以下の研究概要を指示に従って書き換えてください。
前置きのコメントや説明は不要です。
書き換えた文章だけを出力してください。
与えられたテキストに含まれる情報を削除・追加せず、内容を正確に保持したまま、文章の構造を大きく崩さずに、自然な日本語でわかりやすく書き換えてください。専門用語が出てきた場合は、必要に応じて括弧などで短い説明を加え、高校生でも意味が理解できるようにしてください。専門用語の言い換えも可能ですが、意味が変わらないよう注意し、説明が難しい場合はそのまま使って簡単な補足を添えてください。特に医療用語に関しては丁寧に説明・補足をしてください。また、文章を堅苦しくしすぎず、親しみやすい言い回しを心がけてください。テキストの正誤については判断せず、与えられた情報を忠実に取り扱ってください。
"""

for i, row in df.iterrows():
    original_text = row.get(target_column, "")
    if pd.isna(original_text) or original_text.strip() == "":
        rewritten_list.append("")
        continue

    try:
        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[
                {"role": "system", "content": "以下の研究概要を指示に従って書き換えてください。前置きのコメントや説明は不要です。書き換えた文章だけを出力してください。与えられたテキストに含まれる情報を削除・追加せず、内容を正確に保持したまま、文章の構造を大きく崩さずに、自然な日本語でわかりやすく書き換えてください。専門用語が出てきた場合は、必要に応じて括弧などで短い説明を加え、高校生でも意味が理解できるようにしてください。専門用語の言い換えも可能ですが、意味が変わらないよう注意し、説明が難しい場合はそのまま使って簡単な補足を添えてください。特に医療用語に関しては丁寧に説明・補足をしてください。また、文章を堅苦しくしすぎず、親しみやすい言い回しを心がけてください。テキストの正誤については判断せず、与えられた情報を忠実に取り扱ってください。
"},
                {"role": "user", "content": original_text}
            ],
            temperature=0.5
        )
        rewritten_text = response.choices[0].message.content.strip()
    except Exception as e:
        rewritten_text = f"エラー発生: {e}"

    rewritten_list.append(rewritten_text)

# 新しい列を追加
df[output_column] = rewritten_list

# 新しいCSVとして保存
df.to_csv(output_file, index=False, encoding="utf-8-sig")

print(f"完了：{output_file} に保存されました。")