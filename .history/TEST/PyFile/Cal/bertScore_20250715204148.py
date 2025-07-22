# -*- coding: utf-8 -*-
import pandas as pd
import argparse
from bert_score import score
import torch
from tqdm import tqdm
import os
from datetime import datetime

# --- 設定項目 ---
REFERENCE_COLUMN = "人手修正"
ID_COLUMN = "ID"  # IDを特定するための列名
SCORE_PREFIX = "BERTScore"
MODEL_TYPE = 'tohoku-nlp/bert-base-japanese-v3'

def calculate_scores(input_path: str, output_dir: str):
    """
    CSVファイルを読み込み、BERTScoreを計算して結果のみを新しいCSVファイルに保存する。
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_filename = f"{timestamp}_BERTScore.csv"
    output_path = os.path.join(output_dir, output_filename)
    os.makedirs(output_dir, exist_ok=True)

    try:
        df = pd.read_csv(input_path)
        print(f"入力ファイル '{input_path}' を読み込みました。")
    except FileNotFoundError:
        print(f"エラー: 入力ファイルが見つかりません: {input_path}")
        return
    except Exception as e:
        print(f"ファイルの読み込み中にエラーが発生しました: {e}")
        return

    # --- ★★★ 変更点：結果だけを格納するリストを準備 ★★★ ---
    results_data = []

    # 基準列とID列以外のすべての列を比較対象とする
    if REFERENCE_COLUMN not in df.columns or ID_COLUMN not in df.columns:
        print(f"エラー: 基準列 '{REFERENCE_COLUMN}' またはID列 '{ID_COLUMN}' が入力ファイルに見つかりません。")
        return
    candidate_columns = [col for col in df.columns if col not in [REFERENCE_COLUMN, ID_COLUMN]]
    print(f"基準列: '{REFERENCE_COLUMN}'")
    print(f"比較対象の列: {candidate_columns}")
    
    # 「人手修正」列が空でない行だけを処理対象にする
    df_to_process = df.dropna(subset=[REFERENCE_COLUMN])
    df_to_process = df_to_process[df_to_process[REFERENCE_COLUMN].str.strip() != '']
    
    if df_to_process.empty:
        print("警告: 「人手修正」列にデータが含まれている行がありません。")
    else:
        print(f"{len(df_to_process)}行のデータを処理します...")
        for index, row in tqdm(df_to_process.iterrows(), total=len(df_to_process), desc="BERTScore計算中"):
            # --- ★★★ 変更点：1行分の結果を保持する辞書を作成 ★★★ ---
            row_result = {ID_COLUMN: row[ID_COLUMN]}
            reference_text = row[REFERENCE_COLUMN]
            
            for candidate_col in candidate_columns:
                candidate_text = row[candidate_col]

                if pd.isna(candidate_text) or str(candidate_text).strip() == '':
                    continue
                
                try:
                    P, R, F1 = score(
                        [str(candidate_text)], 
                        [str(reference_text)], 
                        model_type=MODEL_TYPE, 
                        num_layers=12,
                        lang='ja',
                        verbose=False
                    )
                    # --- ★★★ 変更点：結果を辞書に格納 ★★★ ---
                    row_result[f'{SCORE_PREFIX}_P_{candidate_col}'] = P.item()
                    row_result[f'{SCORE_PREFIX}_R_{candidate_col}'] = R.item()
                    row_result[f'{SCORE_PREFIX}_F1_{candidate_col}'] = F1.item()

                except Exception as e:
                    print(f"\n行 {index} の処理中にエラーが発生しました: {e}")
                    row_result[f'{SCORE_PREFIX}_F1_{candidate_col}'] = f"ERROR: {e}"
            
            # --- ★★★ 変更点：1行分の結果をリストに追加 ★★★ ---
            results_data.append(row_result)

    # --- ★★★ 変更点：結果リストから新しいデータフレームを作成して保存 ★★★ ---
    if results_data:
        results_df = pd.DataFrame(results_data)
        try:
            results_df.to_csv(output_path, index=False, encoding='utf-8-sig')
            print(f"\n完了！処理結果が '{output_path}' に保存されました。")
        except Exception as e:
            print(f"ファイル書き込み中にエラーが発生しました: {e}")
    else:
        print("処理対象のデータがなかったため、ファイルは出力されませんでした。")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="CSV内のテキストに対してBERTScoreを計算します。'人手修正'列を基準とし、他の全列と比較します。")
    parser.add_argument("input_file", type=str, help="入力CSVファイルのパス")
    # The typo was here
    parser.add_argument("output_dir", type=str, help="結果を保存する出力先ディレクトリのパス")
    
    args = parser.parse_args()
    
    calculate_scores(args.input_file, args.output_dir)