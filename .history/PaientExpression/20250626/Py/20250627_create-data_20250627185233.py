import sys
import datetime
import pandas as pd

def filter_excel_data(input_file):
    """
    指定された条件に基づいてExcelのデータをフィルタリングし、新しいCSVファイルに保存する関数。

    Args:
        input_file (str): 入力Excelファイルへのパス。
    """
    try:
        # Excelファイルを読み込む（1行目をヘッダーとして使用）
        df = pd.read_excel(input_file)

        # 列名に含まれる可能性のある前後のスペースを削除
        df.columns = df.columns.str.strip()

        # オブジェクト型（主に文字列）の列から前後のスペースを削除
        for col in df.select_dtypes(include=['object']).columns:
            df[col] = df[col].str.strip()

    except FileNotFoundError:
        print(f"エラー: ファイル '{input_file}' が見つかりません。")
        sys.exit(1)
    except Exception as e:
        print(f"ファイルの読み込み中にエラーが発生しました: {e}")
        sys.exit(1)


    # --- フィルタリング条件 ---
    # 1. 出現形に'-1'または'ERR'が含まれていない
    #    .astype(str) を使い、数値と文字列が混在していてもエラーなく比較できるようにする
    condition1 = ~df['出現形'].astype(str).isin(['-1', 'ERR'])

    # 2. 正規形に'-1'または'ERR'が含まれていない
    condition2 = ~df['正規形'].astype(str).isin(['-1', 'ERR'])

    # 3. 正規形_flagが'S', 'A', 'B', 'C'のいずれか
    condition3 = df['正規形_flag'].isin(['S', 'A', 'B', 'C'])

    # 4. TREE列に'R'が含まれている（'R'がないセル(NaN)は除外）
    condition4 = df['TREE'].str.contains('R', na=False)


    # 全ての条件を結合してデータを抽出
    filtered_df = df[condition1 & condition2 & condition3 & condition4]

    # --- 出力処理 ---
    # 現在の日時を取得して出力ファイル名を生成
    now = datetime.datetime.now()
    # 出力はCSVファイルとする
    output_file = f"filtered_data_{now.strftime('%Y%m%d_%H%M%S')}.csv"

    # 新しいCSVファイルとして保存（UTF-8で保存）
    # Excelで開くことを考慮し、文字化けしにくい'utf-8-sig'を指定
    filtered_df.to_csv(output_file, index=False, encoding='utf-8-sig')

    print("処理が完了しました。")
    print(f"入力ファイル: {input_file}")
    print(f"抽出件数: {len(filtered_df)}件")
    print(f"出力ファイル: {output_file}")


if __name__ == "__main__":
    # コマンドライン引数のチェック
    if len(sys.argv) < 2:
        print("使い方: python filter_excel_script.py <入力Excelファイル名>")
        sys.exit(1)

    # 引数から入力ファイル名を取得
    input_filename = sys.argv[1]
    filter_excel_data(input_filename)