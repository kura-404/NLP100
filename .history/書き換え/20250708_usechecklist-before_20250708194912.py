import os
import sys
import json
import pandas as pd
from datetime import datetime
from tqdm import tqdm

# ========= 設定 =========
MODEL = "gpt-4.1-mini"

# ========= チェックリストに基づくプロンプト =========
SYSTEM_PROMPT = """
以下の6つの観点に基づいたチェックリストすべてを満たすように、与えられた成果概要を書き換えてください。  
出力には「書き換えた成果概要のみ」を記載してください。解説や前置きは不要です。

---

【1. 文章の書き方についてのポイント】  
① 能動態や肯定形で記述しているか  
② 理解しやすい数字を使っているか  
③ 重要な情報を最初に記述しているか  

---

【2. 資料の読みやすさについてのポイント】  
④ 医療用語や専門用語、略語、難解語、難しい漢字を使っていないか  
⑤ それぞれの文は長くないか（40文字ぐらいまで）  
⑥ 各段落の長さは適当か（200〜300文字程度）  
⑦ 漢字が多すぎないか  

---

【3. 資料全体の見やすさについてのポイント】  
⑧ 見出しや箇条書きを使っているか  
⑨ 文字サイズ、行間、余白などを意識した見やすいレイアウトか  
⑩ 伝えたい情報をわかりやすい言葉や図解的表現（図表・イラスト的記述）で示しているか  

---

【4. 絶対に押さえるべきポイント】  
① 結果の新規性と重要性を正確に伝えているか（誇張しすぎない、期待を煽らない）  
② 研究の進捗段階を明確に書いているか（例：動物実験／治験など）  
③ 誤解を生まないわかりやすいタイトル・目的を明記しているか  

---

【5. できるだけ押さえるべきポイント】  
④ 研究デザインに言及しているか  
⑤ 因果関係を曖昧にせず論理的に記述しているか  
⑥ 不確かさを明示しているか  
⑦ メリットとデメリットを正確にバランスよく述べているか  
⑧ 情報が多すぎたり、不要な情報が含まれていないか  

---

【6. 時と場合によって押さえるべきポイント】  
⑨ 利益相反（COI）について明示しているか（必要な場合）  
⑩ 研究の信頼性を裏付ける根拠（倫理審査・治験登録など）を記載しているか（必要な場合）  

---

これらの観点をすべて考慮し、以下の成果概要を分かりやすく適切に書き直してください。
"""

# ========= 引数処理 =========
if len(sys.argv) != 3:
    print("❌ 使用法: python script.py 入力ファイル.xlsx 出力ディレクトリ")
    sys.exit(1)

input_path = sys.argv[1]
output_base_dir = sys.argv[2]
filename_noext = os.path.splitext(os.path.basename(input_path))[0]

OUTPUT_DIR = os.path.join(output_base_dir, "csv")
BATCH_INPUT_DIR = os.path.join(output_base_dir, "batch_input")
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(BATCH_INPUT_DIR, exist_ok=True)

# ========= ファイル読み込み =========
df = pd.read_excel(input_path)
df.columns = df.columns.str.strip()

# ========= 必要な列の確認 =========
if "ID" not in df.columns or "生成された成果概要" not in df.columns:
    print("❌ 入力ファイルに 'ID' または '生成された成果概要' 列が存在しません。")
    sys.exit(1)

# ========= JSONL生成 =========
jsonl_path = os.path.join(BATCH_INPUT_DIR, f"{filename_noext}_batch_input.jsonl")
output_path = os.path.join(OUTPUT_DIR, f"{filename_noext}_rewritten_output.csv")

records = []
with open(jsonl_path, "w", encoding="utf-8") as fout:
    for _, row in tqdm(df.iterrows(), total=len(df), desc="バッチ入力生成中"):
        task_id = str(row["ID"]).strip()
        before = str(row["生成された成果概要"]).strip()

        prompt_obj = {
            "custom_id": task_id,
            "method": "POST",
            "url": "/v1/chat/completions",
            "body": {
                "model": MODEL,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT.strip()},
                    {"role": "user", "content": before}
                ],
                "temperature": 0.5
            }
        }
        fout.write(json.dumps(prompt_obj, ensure_ascii=False) + "\n")

        records.append({
            "ID": task_id,
            "生成された成果概要": "",
            "生成された成果概要（プロンプトによる書き換えbefore）": before
        })

print(f"✅ バッチ入力ファイル作成完了: {jsonl_path}")

# ========= 空の出力テンプレートをCSVで生成 =========
df_out = pd.DataFrame(records)
df_out = df_out[["ID", "生成された成果概要", "生成された成果概要（プロンプトによる書き換えbefore）"]]
df_out.to_csv(output_path, index=False, encoding="utf-8-sig")
print(f"✅ 出力テンプレートCSV作成済: {output_path}")
