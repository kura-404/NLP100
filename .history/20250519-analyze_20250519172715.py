import pandas as pd
import os
import glob

# ==== 設定：フォルダパスを変更して使ってください ====
input_dir = "/Users/kuramotomana/Test/split_by_year"  # 元CSVが入っているフォルダ
output_dir = "/Users/kuramotomana/Test/analysis_result"  # 結果CSVの保存先

# ==== 出力先ディレクトリを作成 ====
os.makedirs(output_dir, exist_ok=True)

# ==== 処理開始 ====
csv_files = glob.glob(os.path.join(input_dir, "*.csv"))

for file_path in csv_files:
    try:
        file_name = os.path.splitext(os.path.basename(file_path))[0]
        
        # 安全に読み込む（文字化け・改行対策含む）
        df = pd.read_csv(file_path, engine='python', encoding='utf-8', on_bad_lines='skip')

        # 欠損値
        missing_counts = df.isnull().sum()
        missing_counts.name = '欠損値数'

        # 各セルの文字数
        char_len_df = df.fillna('').astype(str).applymap(len)

        # 文字数統計
        text_stats = char_len_df.describe().T[['mean', 'std', 'min', '50%', 'max']]
        text_stats = text_stats.rename(columns={
            'mean': '平均文字数',
            'std': '標準偏差',
            'min': '最短文字数',
            '50%': '中央値',
            'max': '最長文字数'
        })

        # 結合
        summary = pd.concat([missing_counts, text_stats], axis=1)

        # レコード数の行を追加（最下行に"__レコード数__"として追加）
        record_count = len(df)
        summary.loc['__レコード数__'] = [record_count] + [None] * (summary.shape[1] - 1)

        # 保存
        output_path = os.path.join(output_dir, f"{file_name}_summary.csv")
        summary.round(1).to_csv(output_path, encoding="utf-8-sig")
        print(f"✅ 保存完了: {output_path}")

    except Exception as e:
        print(f"❌ エラー（{file_path}）: {e}")