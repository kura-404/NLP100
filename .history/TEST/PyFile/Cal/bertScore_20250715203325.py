# -*- coding: utf-8 -*-
import pandas as pd
import argparse
from bert_score import score
import torch
from tqdm import tqdm

# --- 設定項目 ---
# 比較の基準となる列
REFERENCE_COLUMN = "人手修正"
# 結果を保存する際の新しい列名のプレフィックス
SCORE_PREFIX = "BERTScore"
# 使用するBERTモデル
MODEL_TYPE = 'tohoku-nlp/bert-base-japanese-v3'

def calculate_scores(input_path: str, output_path: str):
    """
    CSVファイルを読み込み、BERTScoreを計算して新しいCSVファイルに保存する。
    """
    # --- 1. CSVファイルの読み込み ---
    try:
        df = pd.read_csv(input_path)
        print(f"入力ファイル '{input_path}' を読み込みました。")
    except FileNotFoundError:
        print(f"エラー: 入力ファイルが見つかりません: {input_path}")
        return
    except Exception as e:
        print(f"ファイルの読み込み中にエラーが発生しました: {e}")
        return

    # ★★★ 変更点：比較対象の列を動的に決定 ★★★
    if REFERENCE_COLUMN not in df.columns:
        print(f"エラー: 基準列 '{REFERENCE_COLUMN}' が入力ファイルに見つかりません。")
        return
    # 「人手修正」列以外のすべての列を比較対象とする
    candidate_columns = [col for col in df.columns if col != REFERENCE_COLUMN]
    print(f"基準列: '{REFERENCE_COLUMN}'")
    print(f"比較対象の列: {candidate_columns}")
    
    # --- 2. 結果を保存するための新しい列を準備 ---
    for col in candidate_columns:
        df[f'{SCORE_PREFIX}_P_{col}'] = None
        df[f'{SCORE_PREFIX}_R_{col}'] = None
        df[f'{SCORE_PREFIX}_F1_{col}'] = None

    # --- 3. 「人手修正」列が空でない行だけを処理対象にする ---
    df_to_process = df.dropna(subset=[REFERENCE_COLUMN])
    df_to_process = df_to_process[df_to_process[REFERENCE_COLUMN].str.strip() != '']
    
    if df_to_process.empty:
        print("警告: 「人手修正」列にデータが含まれている行がありません。処理をスキップします。")
    else:
        print(f"{len(df_to_process)}行のデータを処理します...")
        # --- 4. 1行ずつループしてスコアを計算 ---
        for index, row in tqdm(df_to_process.iterrows(), total=len(df_to_process), desc="BERTScore計算中"):
            reference_text = row[REFERENCE_COLUMN]
            
            # 各候補列に対して計算
            for candidate_col in candidate_columns:
                candidate_text = row[candidate_col]

                if pd.isna(candidate_text) or str(candidate_text).strip() == '':
                    continue
                
                try:
                    P, R, F1 = score(
                        [str(candidate_text)], 
                        [str(reference_text)], 
                        model_type=MODEL_TYPE, 
                        lang='ja',
                        verbose=False
                    )
                    
                    df.loc[index, f'{SCORE_PREFIX}_P_{candidate_col}'] = P.item()
                    df.loc[index, f'{SCORE_PREFIX}_R_{candidate_col}'] = R.item()
                    df.loc[index, f'{SCORE_PREFIX}_F1_{candidate_col}'] = F1.item()

                except Exception as e:
                    print(f"\n行 {index} の処理中にエラーが発生しました: {e}")
                    df.loc[index, f'{SCORE_PREFIX}_F1_{candidate_col}'] = f"ERROR: {e}"

    # --- 5. 結果を新しいCSVファイルに保存 ---
    try:
        df.to_csv(output_path, index=False, encoding='utf-8-sig')
        print(f"\n完了！すべての処理結果が '{output_path}' に保存されました。")
    except Exception as e:
        print(f"ファイル書き込み中にエラーが発生しました: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="CSV内のテキストに対してBERTScoreを計算します。'人手修正'列を基準とし、他の全列と比較します。")
    parser.add_argument("input_file", type=str, help="入力CSVファイルのパス")
    parser.add_argument("output_file", type=str, help="結果を保存する出力CSVファイルのパス")
    f
    args = parser.parse_args()
    
    calculate_scores(args.input_file, args.output_file)