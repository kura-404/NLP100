import pandas as pd
import os

# 入力ファイルパス
input_file = "/Users/kuramotomana/Test/20250519-厚労科研.csv"

# 出力ディレクトリ
output_dir = "/Users/kuramotomana/Test/split_by_year"
os.makedirs(output_dir, exist_ok=True)

try:
    # 1. 安全に読み込み（崩れた行をwarnで回避）
    df = pd.read_csv(
        input_file,
        engine="python",
        encoding="utf-8",
        quotechar='"',
        on_bad_lines="warn"
    )

    # 2. セル内の改行（\nや\r）をすべて空白に置換
    df = df.applymap(lambda x: str(x).replace('\n', ' ').replace('\r', ' ') if pd.notnull(x) else x)

    # 3. 年度ごとに分割保存
    if "研究年度" in df.columns:
        for year, group in df.groupby("研究年度"):
            safe_year = str(year).replace("/", "_").replace("（", "(").replace("）", ")")
            output_path = os.path.join(output_dir, f"年度_{safe_year}.csv")
            group.to_csv(output_path, index=False, encoding="utf-8-sig")
            print(f"✅ 保存: {output_path}")
        print(f"\n📁 年度ごとのCSVが {output_dir} に保存されました。")
    else:
        print("❌ エラー：「研究年度」列が見つかりませんでした。")

except Exception as e:
    print(f"❌ 処理エラー: {e}")
    