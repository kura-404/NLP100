import os
import sys
import pandas as pd
from tqdm import tqdm
from datetime import datetime
from openai import OpenAI

# ========= 設定 =========
MODEL = "gpt-4.1-mini"
SYSTEM_PROMPT = """
以下の成果概要を指示に従って書き換えてください。
前置きのコメントや説明は不要です。書き換えた文章だけを出力してください。
与えられたテキストに含まれる情報を削除・追加せず、内容を正確に保持したまま、文章の構造を大きく崩さずに、自然な日本語でわかりやすく書き換えてください。
専門用語が出てきた場合は、必要に応じて括弧などで短い説明を加え、高校生でも意味が理解できるようにしてください。専門用語の言い換えも可能ですが、意味が変わらないよう注意し、説明が難しい場合はそのまま使って簡単な補足を添えてください。特に医療用語に関しては丁寧に説明・補足をしてください。また、文章を堅苦しくしすぎず、親しみやすい言い回しを心がけてください。テキストの正誤については判断せず、与えられた情報を忠実に取り扱ってください。
"""

# ========= メイン処理 =========
if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("❌ 使用方法: python スクリプト名.py 入力ファイル 出力ディレクトリ")
        sys.exit(1)

    input_path = sys.argv[1]
    output_dir = sys.argv[2]
    os.makedirs(output_dir, exist_ok=True)

    df = pd.read_excel(input_path)
    if "ID" not in df.columns or "生成された成果概要" not in df.columns:
        print("❌ 必要な列（ID、生成された成果概要）が含まれていません。")
        sys.exit(1)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = os.path.join(output_dir, f"rewritten_prompt_{timestamp}.csv")

    from openai import OpenAI
    client = OpenAI()

    results = []
    for _, row in tqdm(df.iterrows(), total=len(df), desc="✅ 書き換え処理中"):
        before_text = row.get("生成された成果概要", "")
        task_id = row.get("ID", "")

        try:
            res = client.chat.completions.create(
                model=MODEL,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": before_text}
                ]
            )
            after_text = res.choices[0].message.content.strip()
        except Exception as e:
            after_text = f"エラー: {e}"

        results.append({
            "ID": task_id,
            "オリジナル": before_text,
            "改良プロンプト": after_text
        })

    pd.DataFrame(results).to_csv(output_file, index=False, encoding="utf-8-sig")
    print(f"✅ 出力完了: {output_file}")
