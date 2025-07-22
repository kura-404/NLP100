import os
import sys
import pandas as pd
from datetime import datetime

def main():
    if len(sys.argv) < 3:
        print("❗ 使用法: python check_missing_excel.py <入力ディレクトリ> <出力ディレクトリ>")
        sys.exit(1)

    input_dir = sys.argv[1]
    output_dir = sys.argv[2]

    if not os.path.isdir(input_dir):
        print(f"❗ エラー: 入力ディレクトリが存在しません: {input_dir}")
        sys.exit(1)

    if not os.path.isdir(output_dir):
        print(f"📁 出力ディレクトリが存在しません。作成します: {output_dir}")
        os.makedirs(output_dir)

    excel_files = [f for f in os.listdir(input_dir) if f.endswith(".xlsx")]
    if not excel_files:
        print("⚠️ 入力ディレクトリにExcelファイル（.xlsx）が見つかりません。")
        sys.exit(0)

    results = []

    for excel_file in excel_files:
        file_path = os.path.join(input_dir, excel_file)
        try:
            xl = pd.ExcelFile(file_path)
            for sheet_name in xl.sheet_names:
                try:
                    df = xl.parse(sheet_name, nrows=1001)
                    missing_counts = df.isnull().sum()
                    for col, count in missing_counts.items():
                        results.append({
                            "ファイル名": excel_file,
                            "シート名": sheet_name,
                            "列名": col,
                            "欠損値数": int(count)
                        })
                except Exception as e:
                    print(f"⚠️ シート読み込みエラー: {excel_file} - {sheet_name} → {e}")
        except Exception as e:
            print(f"⚠️ ファイル読み込みエラー: {excel_file} → {e}")

    if results:
        df_result = pd.DataFrame(results)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f"missing_counts_{timestamp}.csv"
        output_path = os.path.join(output_dir, output_filename)
        df_result.to_csv(output_path, index=False, encoding="utf-8-sig")
        print(f"✅ 集計結果を出力しました: {output_path}")
    else:
        print("⚠️ 欠損値集計結果がありません。")

if __name__ == "__main__":
    main()