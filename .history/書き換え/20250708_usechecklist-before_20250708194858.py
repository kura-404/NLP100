import sys
import json
import pandas as pd
from datetime import datetime

# ========= 引数確認 =========
if len(sys.argv) != 3:
    print("❌ 使用法: python merge_response.py 応答jsonl テンプレートcsv")
    sys.exit(1)

response_file = sys.argv[1]
template_csv = sys.argv[2]
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
output_csv = template_csv.replace(".csv", f"_with_result_{timestamp}.csv")

# ========= 応答ファイル読み込み =========
responses = {}
with open(response_file, "r", encoding="utf-8") as f:
    for line in f:
        obj = json.loads(line)
        if "custom_id" in obj and "response" in obj:
            try:
                content = obj["response"]["body"]["choices"][0]["message"]["content"].strip()
                responses[obj["custom_id"]] = content
            except Exception as e:
                responses[obj["custom_id"]] = f"エラー: {e}"

# ========= テンプレートCSV読み込み =========
df = pd.read_csv(template_csv, encoding="utf-8-sig")

# ========= 列の入れ替え：生成された成果概要 ← before、書き換え後 ← API出力 =========
df["生成された成果概要（プロンプトによる書き換えbefore）"] = df["生成された成果概要"]
df["生成された成果概要"] = df["ID"].astype(str).map(responses).fillna("（応答なし）")

# ========= 書き出し =========
df.to_csv(output_csv, index=False, encoding="utf-8-sig")
print(f"✅ 書き換え結果をマージしました: {output_csv}")