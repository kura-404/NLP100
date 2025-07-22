import os
import sys
import pandas as pd
from tqdm import tqdm
from datetime import datetime
from openai import OpenAI

# ========= 設定 =========
MODEL = "gpt-4.1-mini"
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
    output_file = os.path.join(output_dir, f"{timestamp}_rewritten_prompt.csv")

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
