import os
import pandas as pd
from openai import OpenAI
from tqdm import tqdm

# ========== 🔧 設定 ==========
MODE = "test"  # "test" または "prod"
TARGET_FILE = "/Users/kuramotomana/Test/LifeStory_2018_season1.xlsx"
TARGET_COLUMN = "列名をここに"  # 例: "Sadness"
TARGET_DIR = "path/to/excel_files"

OUTPUT_DIR = "output_excel"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ========== 🧠 分類プロンプト（共通） ==========
SYSTEM_PROMPT = (
    "あなたはこれからテキスト分類に取り組んでください。以下の要件に従って、入力リストの各文章を分類してください。\n\n"
    "【分類タスク】\n"
    "– ラベル: パートナー／家族／ペット／友人／同僚／それ以外の人物／AI／登場なし\n"
    "– 複数のラベルに当てはまる場合は、複数ラベルを空白区切りで出力してください\n"
    "– 各分類は1行ずつ、該当するラベルのみを出力してください（例：「家族 友人」）\n"
    "– ラベルが1つも該当しない場合は「登場なし」と記述してください"
)

# ========== 🔌 OpenAI ==========
client = OpenAI()

def classify_list(cell_list: list[str]) -> list[str]:
    """1列まとめて分類（共通処理）"""
    prompt = "\n".join(cell_list)
    try:
        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ],
            max_tokens=12000
        )
        output = response.choices[0].message.content.strip().split("\n")
        if len(output) < len(cell_list):
            print(f"⚠️ 出力不足: {len(output)} / {len(cell_list)} 件")
        return output[:len(cell_list)]
    except Exception as e:
        print(f"❌ APIエラー: {str(e)}")
        return ["エラー"] * len(cell_list)

def save_output(base_name, col, cell_list, labels):
    """結果をExcelで保存"""
    safe_col = str(col).replace("/", "_").replace("\\", "_")
    filename = f"{base_name}-{safe_col}.xlsx"
    path = os.path.join(OUTPUT_DIR, filename)
    df_out = pd.DataFrame({"元の値": cell_list, "分類ラベル": labels})
    df_out.to_excel(path, index=False)
    print(f"✅ 出力完了: {filename}")

# ========== ▶️ 実行処理 ==========
if MODE == "test":
    print("🧪 テストモード開始（1列=1リクエスト）")
    df = pd.read_excel(TARGET_FILE)
    if TARGET_COLUMN not in df.columns:
        raise ValueError(f"列「{TARGET_COLUMN}」が存在しません")

    series = df[TARGET_COLUMN].dropna().astype(str)
    cell_list = series.tolist()
    print(f"▶️ 処理中: {TARGET_FILE} - 列「{TARGET_COLUMN}」 ({len(cell_list)}行)")

    labels = classify_list(cell_list)
    save_output(os.path.splitext(os.path.basename(TARGET_FILE))[0], TARGET_COLUMN, cell_list, labels)

elif MODE == "prod":
    print("📦 本番モード開始（1列=1リクエスト、4ファイル=1バッチ）")
    excel_files = [f for f in os.listdir(TARGET_DIR) if f.endswith(".xlsx")]

    for batch_idx in range(0, len(excel_files), 4):
        batch_files = excel_files[batch_idx:batch_idx + 4]
        print(f"\n🚀 バッチ {batch_idx // 4 + 1} 開始：{batch_files}")

        for file_name in batch_files:
            file_path = os.path.join(TARGET_DIR, file_name)
            try:
                df = pd.read_excel(file_path)
            except Exception as e:
                print(f"❌ 読み込みエラー: {file_name} - {str(e)}")
                continue

            base_name = os.path.splitext(file_name)[0]
            for col in df.columns:
                series = df[col].dropna().astype(str)
                if series.empty:
                    print(f"⚠️ 列「{col}」は空です。スキップ。")
                    continue

                cell_list = series.tolist()
                print(f"▶️ 処理中: {file_name} - 列「{col}」 ({len(cell_list)}行)")

                labels = classify_list(cell_list)
                save_output(base_name, col, cell_list, labels)

else:
    raise ValueError("MODE は 'test' または 'prod' を指定してください")