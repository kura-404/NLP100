import sys
import datetime
import pandas as pd
import pathlib

def filter_excel_data(input_file):
    """
    指定された条件に基づいてExcelのデータをフィルタリングし、
    1つ上の階層の'Output'フォルダに新しいCSVファイルとして保存する関数。
    正規形列に';'が含まれる場合は行を分割する。

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

    # --- ★★★ 正規形列の分割処理（ここが追加・変更点） ★★★ ---
    # 正規形が空(NaN)の場合にエラーが出ないよう、文字列に変換してから分割
    df['正規形'] = df['正規形'].astype(str).str.split(';')

    # explodeを使ってリストの要素を行に展開
    df = df.explode('正規形', ignore_index=True)

    # 分割後の正規形の前後のスペースを再度削除
    df['正規形'] = df['正規形'].str.strip()
    # ---------------------------------------------------------

    # --- フィルタリング条件 ---
    # 1. 出現形に'-1'または'ERR'が含まれていない
    condition1 = ~df['出現形'].astype(str).isin(['-1', 'ERR'])

    # 2. 正規形に'-1'または'ERR'が含まれていない (分割後の各正規形が対象)
    condition2 = ~df['正規形'].astype(str).isin(['-1', 'ERR'])

    # 3. 正規形_flagが'S', 'A', 'B', 'C'のいずれか
    condition3 = df['正規形_flag'].isin(['S', 'A', 'B', 'C'])

    # 4. TREE列に'R'が含まれている（'R'がないセル(NaN)は除外）
    condition4 = df['TREE'].str.contains('R', na=False)


    # 全ての条件を結合してデータを抽出
    filtered_df = df[condition1 & condition2 & condition3 & condition4]

    # --- 出力処理 ---
    try:
        # スクリプト自身の絶対パスを取得
        script_path = pathlib.Path(__file__).resolve()
        # 出力ディレクトリのパスを構築（スクリプトの親ディレクトリ/Output）
        output_dir = script_path.parent.parent / 'Output'
    except NameError:
        # 対話モードなどで__file__が定義されていない場合のフォールバック
        output_dir = pathlib.Path.cwd().parent / 'Output'

    # 出力ディレクトリが存在しない場合は作成
    output_dir.mkdir(parents=True, exist_ok=True)

    # 現在の日時を取得して出力ファイル名を生成
    now = datetime.datetime.now()
    filename = f"filtered_data_{now.strftime('%Y%m%d_%H%M%S')}.csv"
    
    # 完全な出力ファイルパス
    output_filepath = output_dir / filename

    # 新しいCSVファイルとして保存（UTF-8で保存）
    # Excelで開くことを考慮し、文字化けしにくい'utf-8-sig'を指定
    filtered_df.to_csv(output_filepath, index=False, encoding='utf-8-sig')

    print("処理が完了しました。")
    print(f"入力ファイル: {input_file}")
    print(f"抽出件数: {len(filtered_df)}件 (正規形の分割後)")
    print(f"出力ファイル: {output_filepath}")


if __name__ == "__main__":
    # コマンドライン引数のチェック
    if len(sys.argv) < 2:
        print("使い方: python filter_excel_script.py <入力Excelファイル名>")
        sys.exit(1)

    # 引数から入力ファイル名を取得
    input_filename = sys.argv[1]
    filter_excel_data(input_filename)