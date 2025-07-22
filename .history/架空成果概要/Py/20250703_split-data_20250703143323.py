import pandas as pd
import csv
import sys
from datetime import datetime

# === 引数処理 ===
if len(sys.argv) < 2:
    print("⚠️ 入力ファイルを指定してください（例: python split_sentences.py input.xlsx）")
    sys.exit(1)

input_file = sys.argv[1]

# === データ読み込み ===
df = pd.read_excel(input_file)

# === 出力用リスト ===
output_rows = []

for _, row in df.iterrows():
    base_id = str(row["ID"]).strip()
    original_text = str(row["生成された成果概要"]).strip()
    rewritten_text = str(row["書き換え後（LLM）：成果概要"]).strip()

    # 「。」で分割し、文末句点を戻す
    original_sentences = [s.strip() + "。" for s in original_text.split("。") if s.strip()]
    rewritten_sentences = [s.strip() + "。" for s in rewritten_text.split("。") if s.strip()]

    max_len = max(len(original_sentences), len(rewritten_sentences))

    for i in range(max_len):
        output_rows.append({
            "id": f"{base_id}-{i+1}",
            "original_sentence": original_sentences[i] if i < len(original_sentences) else "",
            "rewritten_sentence": rewritten_sentences[i] if i < len(rewritten_sentences) else ""
        })

# === 日時付きファイル名 ===
timestamp = datetime.now().strftime("%Y%m%d_%H%M")
output_file = f"paired_sentences_{timestamp}.csv"

# === CSV出力 ===
with open(output_file, mode="w", newline="", encoding="utf-8-sig") as f:
    writer = csv.DictWriter(f, fieldnames=["id", "original_sentence", "rewritten_sentence"])
    writer.writeheader()
    writer.writerows(output_rows)

print(f"✅ 出力完了: {output_file}")