import pandas as pd
import glob
import os

# 対象のディレクトリを指定（例：'./csv_dir/'）
csv_dir = '/Users/kuramotomana/Test/outputs/csv'
output_file = 'combined.csv'

# すべてのCSVファイルを取得
csv_files = glob.glob(os.path.join(csv_dir, '*.csv'))

# データを格納するリスト
dataframes = []

# 各CSVを読み込んでリストに追加（列が概ね同じことが前提）
for file in csv_files:
    try:
        df = pd.read_csv(file)
        dataframes.append(df)
    except Exception as e:
        print(f"読み込みエラー: {file} - {e}")

# すべてのCSVを縦に結合（列名が一致している場合のみ）
combined_df = pd.concat(dataframes, ignore_index=True)

# 結果をCSVとして出力
#combined_df.to_csv(output_file, index=False)
print(f"結合完了: {output_file}")