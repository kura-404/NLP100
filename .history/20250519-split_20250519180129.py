import pandas as pd
import os

# ==== 設定 ====
input_file = "/Users/kuramotomana/Test/20250519-厚労科研.csv"
output_dir = "/Users/kuramotomana/Test/split_by_year"
os.makedirs(output_dir, exist_ok=True)

try:
    # ==== 安全に読み込み ====
    df = pd.read_csv(
        input_file,
        engine="python",          # 柔軟な読み込み
        encoding="utf-8",         # 必要なら 'utf-8-sig' や 'cp932' に変更
        quotechar='"',            # セル内の改行やカンマを正しく扱う
        on_bad_lines="warn"       # 異常な行をスキップまたは警告
    )

    # ==== 年度列があるか確認してスプリット ====
    if "研究年度" in df.columns:
        for year, group in df.groupby("研究年度"):
            # 年度にスラッシュやカッコがあっても使えるようファイル名を安全化
            safe_year = str(year).replace("/", "_").replace("（", "(").replace("）", ")")
            output_path = os.path.join(output_dir, f"年度_{safe_year}.csv")
            group.to_csv(output_path, index=False, encoding="utf-8-sig")
            print(f"✅ 保存: {output_path}")
        print(f"\n📁 年度ごとのCSVが {output_dir} に保存されました。")
    else:
        print("❌ エラー：「研究年度」列が見つかりませんでした。")

except Exception as e:
    print(f"❌ ファイル読み込み中にエラー発生: {e}")