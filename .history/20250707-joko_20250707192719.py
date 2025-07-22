import os
import pandas as pd
from openai import OpenAI

# OpenAIクライアント初期化
client = OpenAI()

# 🔧 テスト対象ファイルと列名を指定
TARGET_FILE = "path/to/excel_files/テストファイル.xlsx"  # ← ファイルパスを変更
TARGET_COLUMN = "列名をここに"  # ← 実際の列名を指定（例："感想"）

OUTPUT_DIR = "output_excel"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# プロンプト（まとめて分類）
SYSTEM_PROMPT = (
    "あなたはこれからテキスト分類に取り組んでください。以下の要件に従って、入力リストの各文章を分類してください。\n\n"
    "【分類タスク】\n"
    "– ラベル: パートナー／家族／ペット／友人／同僚／それ以外の人物／AI／登場なし\n"
    "– 複数のラベルに当てはまる場合は、複数ラベルを空白区切りで出力してください\n"
    "– 各分類は1行ずつ、該当するラベルのみを出力してください（例：「家族 友人」）\n"
    "– ラベルが1つも該当しない場合は「登場なし」と記述してください"
)

# 📄 ファイル読み込み
df = pd.read_excel(TARGET_FILE)
file_name = os.path.basename(TARGET_FILE)

# 指定列のデータを抽出
if TARGET_COLUMN not in df.columns:
    raise ValueError(f"列「{TARGET_COLUMN}」が見つかりません。列名を確認してください。")

series = df[TARGET_COLUMN].dropna().astype(str)
cell_list = series.tolist()

# 1回のリクエストで分類
user_prompt = "\n".join(cell_list)

try:
    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt}
        ],
        max_tokens=12000
    )

    content = response.choices[0].message.content.strip().split('\n')

    # 出力数不足チェック
    if len(content) < len(cell_list):
        print(f"⚠️ 出力不足: {len(content)} / {len(cell_list)} 件")

    # 出力整形
    output_df = pd.DataFrame({
        "元の値": cell_list,
        "分類ラベル": content[:len(cell_list)]
    })

    # 出力ファイル名
    base_name = os.path.splitext(file_name)[0]
    safe_col = TARGET_COLUMN.replace("/", "_").replace("\\", "_")
    output_filename = f"{base_name}-{safe_col}.xlsx"
    output_path = os.path.join(OUTPUT_DIR, output_filename)

    output_df.to_excel(output_path, index=False, encoding='utf-8')
    print(f"✅ 出力完了: {output_filename}")

except Exception as e:
    print(f"❌ エラー発生: {str(e)}")