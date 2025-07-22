import pandas as pd
import os
import glob

# ==== 設定 ====
input_dir = "/Users/kuramotomana/Test/split_by_year"
output_file = "/Users/kuramotomana/Test/analysis_result/統合レポート.csv"

# ==== 統合用リスト ====
summary_rows = []

# ==== 全CSVファイル処理 ====
csv_files = glob.glob(os.path.join(input_dir, "*.csv"))

for file_path in csv_files:
    try:
        file_name = os.path.splitext(os.path.basename(file_path))[0]
        df = pd.read_csv(file_path, engine='python', encoding='utf-8', on_bad_lines='skip')
        n_rows = len(df)

        # 欠損関連
        non_missing = df.notnull().sum()
        missing = df.isnull().sum()
        missing_rate = (missing / n_rows * 100).round(1)

        # 文字数統計
        char_len_df = df.fillna('').astype(str).applymap(len)
        stats = char_len_df.describe().T[['mean', 'std', 'min', '50%', 'max']]
        stats.columns = ['平均文字数', '標準偏差', '最短文字数', '中央値', '最長文字数']

        # 各列について統合行を構築
        for col in df.columns:
            row = {
                'ファイル名': file_name,
                '列名': col,
                'レコード数': n_rows,
                '存在数': non_missing[col],
                '欠損値数': missing[col],
                '欠損率（％）': missing_rate[col],
                '平均文字数': stats.at[col, '平均文字数'],
                '標準偏差': stats.at[col, '標準偏差'],
                '最短文字数': stats.at[col, '最短文字数'],
                '中央値': stats.at[col, '中央値'],
                '最長文字数': stats.at[col, '最長文字数']
            }
            summary_rows.append(row)

        print(f"✅ 処理完了: {file_name}")

    except Exception as e:
        print(f"❌ エラー（{file_path}）: {e}")

# ==== 統合データを保存 ====
summary_df = pd.DataFrame(summary_rows)
summary_df.to_csv(output_file, index=False, encoding="utf-8-sig")
print(f"\n📊 統合レポート出力完了 → {output_file}")