# -*- coding: utf-8 -*-
import pandas as pd
import argparse
import MeCab
from nltk.translate.bleu_score import sentence_bleu, SmoothingFunction
from tqdm import tqdm
import os
from datetime import datetime
from typing import List

# --- 設定項目 ---
REFERENCE_COLUMN = "人手修正"
ID_COLUMN = "ID"
SCORE_PREFIX = "BLEUScore"

# --- MeCab Tokenizer ---
# MeCabの初期化は一度だけ行う
mecab_tagger = MeCab.Tagger("-Owakati")

class MeCabTokenizer:
    def tokenize(self, text: str) -> List[str]:
        # MeCabのparse結果は最後に改行が含まれることがあるのでstrip()
        wakati_str = mecab_tagger.parse(text).strip()
        return wakati_str.split()

def calculate_bleu(input_path: str, output_dir: str):
    """
    CSVファイルを読み込み、BLEUスコアを計算して結果のみを新しいCSVファイルに保存する。
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_filename = f"{timestamp}_BLEUScore.csv"
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

    tokenizer = MeCabTokenizer()
    smoother = SmoothingFunction().method1 # スムージング関数

    results_data = []

    if REFERENCE_COLUMN not in df.columns or ID_COLUMN not in df.columns:
        print(f"エラー: 基準列 '{REFERENCE_COLUMN}' またはID列 '{ID_COLUMN}' が入力ファイルに見つかりません。")
        return
    candidate_columns = [col for col in df.columns if col not in [REFERENCE_COLUMN, ID_COLUMN]]
    print(f"基準列: '{REFERENCE_COLUMN}'")
    print(f"比較対象の列: {candidate_columns}")

    df_to_process = df.dropna(subset=[REFERENCE_COLUMN])
    df_to_process = df_to_process[df_to_process[REFERENCE_COLUMN].str.strip() != '']

    if df_to_process.empty:
        print("警告: 「人手修正」列にデータが含まれている行がありません。")
    else:
        print(f"{len(df_to_process)}行のデータを処理します...")
        for index, row in tqdm(df_to_process.iterrows(), total=len(df_to_process), desc="BLEUスコア計算中"):
            row_result = {ID_COLUMN: row[ID_COLUMN]}
            
            try:
                # 基準文は一度だけトークナイズする
                reference_text = str(row[REFERENCE_COLUMN])
                ref_tokens = [tokenizer.tokenize(reference_text)]

                for candidate_col in candidate_columns:
                    candidate_text = row.get(candidate_col)

                    if pd.isna(candidate_text) or str(candidate_text).strip() == '':
                        score_val = None
                    else:
                        cand_tokens = tokenizer.tokenize(str(candidate_text))
                        score_val = sentence_bleu(ref_tokens, cand_tokens, smoothing_function=smoother)
                    
                    row_result[f'{SCORE_PREFIX}_{candidate_col}'] = score_val

            except Exception as e:
                print(f"\n行 {index} の処理中にエラーが発生しました: {e}")
                # エラーが起きた行の最初のスコア列にエラーメッセージを記録
                first_score_col = f'{SCORE_PREFIX}_{candidate_columns[0]}'
                row_result[first_score_col] = f"ERROR: {e}"

            results_data.append(row_result)

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
    parser = argparse.ArgumentParser(description="CSV内のテキストに対してBLEUスコアを計算します。'人手修正'列を基準とし、他の全列と比較します。")
    parser.add_argument("input_file", type=str, help="入力CSVファイルのパス")
    parser.add_argument("output_dir", type=str, help="結果を保存する出力先ディレクトリのパス")
    
    args = parser.parse_args()
    
    calculate_bleu(args.input_file, args.output_dir)