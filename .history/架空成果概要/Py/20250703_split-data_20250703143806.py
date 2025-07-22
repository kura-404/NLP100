import pandas as pd
import sys
import os
from datetime import datetime

# === コマンドライン引数の処理 ===
if len(sys.argv) < 3:
    print("⚠️ 使用法: python split_sentences.py <input_file.xlsx> <output_directory>")
    sys.exit(1)

input_file = sys.argv[1]
output_dir = sys.argv[2]

# === データ読み込みと列名整形 ===
df = pd.read_excel(input_file)
df.columns = df.columns.str.strip().str.lower()  # 列名を正規化（小文字＋前後空白除去）

# 必須列を取得
try:
    id_col = "id"
    orig_col = "生成された成果概要".lower()
    rewrite_col = "書き換え後（llm）：成果概要".lower()
except KeyError:
    print("❌ 列名が見つかりません。ファイルを確認してください。")
    print("列名一覧:", df.columns.tolist())
    sys.exit(1)

# === 出力用データ ===
output_rows = []

for _, row in df.iterrows():
    base_id = str(row[id_col]).strip()
    original_text = str(row[orig_col]).strip()
    rewritten_text = str(row[rewrite_col]).strip()

    # 文の分割（句点ごと保持）
    original_sentences = [s.strip() + "。" for s in original_text.split("。") if s.strip()]
    rewritten_sentences = [s.strip() + "。" for s in rewritten_text.split("。") if s.strip()]
    max_len = max(len(original_sentences), len(rewritten_sentences))

    for i in range(max_len):
        output_rows.append({
            "id": f"{base_id}-{i+1}",
            orig_col: original_sentences[i] if i < len(original_sentences) else "",
            rewrite_col: rewritten_sentences[i] if i < len(rewritten_sentences) else ""
        })

# === DataFrame化 + 出力ファイル名作成 ===
output_df = pd.DataFrame(output_rows)
timestamp = datetime.now().strftime("%Y%m%d_%H%M")
output_filename = f"paired_sentences_{timestamp}.xlsx"
output_path = os.path.join(output_dir, output_filename)

# === Excel書き出し ===
output_df.to_excel(output_path, index=False)

print(f"✅ 出力完了: {output_path}")