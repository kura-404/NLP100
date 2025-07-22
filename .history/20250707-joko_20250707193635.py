import os
import pandas as pd
from openai import OpenAI
from tqdm import tqdm

# ========== 🔧 設定 ==========
MODE = "prd"  # "test" または "prod"
TARGET_FILE = "path/to/excel_files/テストファイル.xlsx"
TARGET_COLUMN = "列名をここに"  # 例: "感想"
TARGET_DIR = "path/to/excel_files"

OUTPUT_DIR = "output_excel"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ========== 🧠 分類プロンプト ==========
BATCH_PROMPT = (
    "あなたはこれからテキスト分類に取り組んでください。以下の要件に従って、入力リストの各文章を分類してください。\n\n"
    "【分類タスク】\n"
    "– ラベル: パートナー／家族／ペット／友人／同僚／それ以外の人物／AI／登場なし\n"
    "– 複数のラベルに当てはまる場合は、複数ラベルを空白区切りで出力してください\n"
    "– 各分類は1行ずつ、該当するラベルのみを出力してください（例：「家族 友人」）\n"
    "– ラベルが1つも該当しない場合は「登場なし」と記述してください"
)

SINGLE_PROMPT = (
    "以下の文に登場する人物を分類してください。\n"
    "– ラベル: パートナー／家族／ペット／友人／同僚／それ以外の人物／AI／登場なし\n"
    "– 複数該当する場合は空白で区切って列挙してください。\n"
    "– 出力は分類ラベルのみを返してください（説明不要）。"
)

# ========== 🔌 OpenAI クライアント ==========
client = OpenAI()

def classify_list(cell_list: list[str]) -> list[str]:
    """1列まとめて分類（本番用）"""
    prompt = "\n".join(cell_list)
    try:
        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[
                {"role": "system", "content": BATCH_PROMPT},
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

def classify_single(text: str) -> str:
    """1セルずつ分類（テスト用）"""
    try:
        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[
                {"role": "system", "content": SINGLE_PROMPT},
                {"role": "user", "content": text}
            ],
            max_tokens=200
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"❌ セル処理エラー: {str(e)}")
        return "エラー"

def save_output(base_name, col, cell_list, labels):
    """結果をExcelファイルに保存"""
    safe_col = str(col).replace("/", "_").replace("\\", "_")
    filename = f"{base_name}-{safe_col}.xlsx"
    path = os.path.join(OUTPUT_DIR, filename)
    df_out = pd.DataFrame({"元の値": cell_list, "分類ラベル": labels})
    df_out.to_excel(path, index=False)  # ✅ encoding を削除
    print(f"✅ 出力完了: {filename}")

# ========== ▶️ 実行処理 ==========
if MODE == "test":
    print("🧪 テストモード開始（1列逐次処理）")
    df = pd.read_excel(TARGET_FILE)
    if TARGET_COLUMN not in df.columns:
        raise ValueError(f"列「{TARGET_COLUMN}」が存在しません")

    series = df[TARGET_COLUMN].dropna().astype(str)
    cell_list = series.tolist()
    results = []

    for i, text in enumerate(cell_list, start=1):
        label = classify_single(text)
        print(f"{i:03d} ▶️ テキスト: {text[:30]}... → 分類: {label}")
        results.append(label)

    save_output(os.path.splitext(os.path.basename(TARGET_FILE))[0], TARGET_COLUMN, cell_list, results)

elif MODE == "prod":
    print("📦 本番モード開始（1列＝1リクエスト、4ファイル＝1バッチ）")
    excel_files = [f for f in os.listdir(TARGET_DIR) if f.endswith(".xlsx")]

    for batch_idx in range(0, len(excel_files), 4):
        batch_files = excel_files[batch_idx:batch_idx + 4]
        print(f"\n🚀 バッチ {batch_idx//4 + 1} 開始：{batch_files}")

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