import os
import sys
import pandas as pd
from tqdm import tqdm
from datetime import datetime
from openai import OpenAI

# ========= 設定 =========
MODEL = "gpt-4.1-mini"
SYSTEM_PROMPT = """

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
    output_file = os.path.join(output_dir, f"{timestamp}_rewritten_beforechecklist.csv")

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
            "生成された成果概要（書き換え後）": after_text,
            "生成された成果概要（書き換え前）": before_text
        })

    pd.DataFrame(results).to_csv(output_file, index=False, encoding="utf-8-sig")
    print(f"✅ 出力完了: {output_file}")
