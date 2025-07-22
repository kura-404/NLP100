# -*- coding: utf-8 -*-
import pandas as pd
import argparse
import MeCab
from rouge_score import rouge_scorer, tokenizers
from tqdm import tqdm
import os
from datetime import datetime
from typing import List

# --- 設定項目 ---
REFERENCE_COLUMN = "人手修正"
ID_COLUMN = "ID"
SCORE_PREFIX = "ROUGE-L"

# --- MeCab Tokenizer ---
class MeCabTokenizer(tokenizers.Tokenizer):
    """MeCabを使って日本語をトークン化するカスタムトークナイザー"""
    def __init__(self):
        # MeCabの初期化は一度だけ行う
        self.mecab = MeCab.Tagger("-Owakati")

    def tokenize(self, text: str) -> List[str]:
        # MeCabのparse結果は最後に改行が含まれることがあるのでstrip()
        return self.mecab.parse(text).strip().split()

def calculate_rouge(input_path: str, output_dir: str):
    """
    CSVファイルを読み込み、ROUGE-Lスコアを計算して結果のみを新しいCSVファイルに保存する。
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_filename = f"{timestamp}_ROUGEScore.csv"
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

    # スコア計算器とトークナイザーを初期化
    scorer = rouge_scorer.RougeScorer(
        rouge_types=['rougeL'],
        use_stemmer=False,
        tokenizer=MeCabTokenizer()
    )

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
        for index, row in tqdm(df_to_process.iterrows(), total=len(df_to_process), desc="ROUGE-Lスコア計算中"):
            row_result = {ID_COLUMN: row[ID_COLUMN]}
            
            try:
                reference_text = str(row[REFERENCE_COLUMN])

                for candidate_col in candidate_columns:
                    candidate_text = row.get(candidate_col)

                    if pd.isna(candidate_text) or str(candidate_text).strip() == '':
                        score_p, score_r, score_f = None, None, None
                    else:
                        score = scorer.score(reference_text, str(candidate_text))['rougeL']
                        score_p = score.precision
                        score_r = score.recall
                        score_f = score.fmeasure
                    
                    row_result[f'{SCORE_PREFIX}_P_{candidate_col}'] = score_p
                    row_result[f'{SCORE_PREFIX}_R_{candidate_col}'] = score_r
                    row_result[f'{SCORE_PREFIX}_F1_{candidate_col}'] = score_f

            except Exception as e:
                print(f"\n行 {index} の処理中にエラーが発生しました: {e}")
                first_score_col = f'{SCORE_PREFIX}_F1_{candidate_columns[0]}'
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
    parser = argparse.ArgumentParser(description="CSV内のテキストに対してROUGE-Lスコアを計算します。'人手修正'列を基準とし、他の全列と比較します。")
    parser.add_argument("input_file", type=str, help="入力CSVファイルのパス")
    parser.add_argument("output_dir", type=str, help="結果を保存する出力先ディレクトリのパス")
    
    args = parser.parse_args()
    
    calculate_rouge(args.input_file, args.output_dir)