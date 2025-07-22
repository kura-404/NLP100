#基礎統計量を列ごとに出せる
import pandas as pd
import os
import glob

# ==== 設定パラメータ（適宜変更） ====
input_dir = "/Users/kuramotomana/Test/split_by_year"         # 入力フォルダ（CSVが複数ある場所）
output_dir = "/content/analysis_results"  # 出力フォルダ（結果CSVの保存先）

# ==== 出力先ディレクトリの作成 ====
os.makedirs(output_dir, exist_ok=True)

# ==== CSVファイルをすべて処理 ====
csv_files = glob.glob(os.path.join(input_dir, "*.csv"))

for file_path in csv_files:
    try:
        # 元ファイル名（拡張子なし）
        file_name = os.path.splitext(os.path.basename(file_path))[0]

        # CSV読み込み
        df = pd.read_csv(file_path)

        # 欠損値の数
        missing_counts = df.isnull().sum()
        missing_counts.name = '欠損値数'

        # 各セルの文字数を取得
        char_len_df = df.fillna('').astype(str).applymap(len)

        # 文字数の統計量を取得
        text_stats = char_len_df.describe().T[['mean', 'std', 'min', '50%', 'max']]
        text_stats = text_stats.rename(columns={
            'mean': '平均文字数',
            'std': '標準偏差',
            'min': '最短文字数',
            '50%': '中央値',
            'max': '最長文字数'
        })

        # 欠損値情報と結合
        summary = pd.concat([missing_counts, text_stats], axis=1)

        # 保存パスの組み立て
        output_file = os.path.join(output_dir, f"{file_name}_summary.csv")

        # 保存
        summary.round(1).to_csv(output_file, encoding="utf-8-sig")
        print(f"保存完了: {output_file}")

    except Exception as e:
        print(f"エラー（{file_path}）: {e}")