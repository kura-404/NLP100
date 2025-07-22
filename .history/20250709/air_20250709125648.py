import os
import sys
import pandas as pd
from datetime import datetime

def main():
    if len(sys.argv) < 3:
        print("❗ 使用法: python check_missing_by_column.py <入力ディレクトリ> <出力ディレクトリ>")
        sys.exit(1)

    input_dir = sys.argv[1]
    output_dir = sys.argv[2]

    if not os.path.isdir(input_dir):
        print(f"❗ エラー: 入力ディレクトリが存在しません: {input_dir}")
        sys.exit(1)

    if not os.path.isdir(output_dir):
        print(f"📁 出力ディレクトリが存在しません。作成します: {output_dir}")
        os.makedirs(output_dir)

    csv_files = [f for f in os.listdir(input_dir) if f.endswith(".csv")]
    if not csv_files:
        print("⚠️ 入力ディレクトリにCSVファイルが見つかりません。")
        sys.exit(0)

    results = []

    for csv_file in csv_files:
        file_path = os.path.join(input_dir, csv_file)
        try:
            df = pd.read_csv(file_path, nrows=1001)  # 1001行目まで読み込み
            missing_counts = df.isnull().sum()  # 各列の欠損値数
            for col, count in missing_counts.items():
                results.append({
                    "ファイル名": csv_file,
                    "列名": col,
                    "欠損値数": int(count)
                })
        except Exception as e:
            print(f"⚠️ エラー: {csv_file} の読み込み中に問題が発生しました → {e}")

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