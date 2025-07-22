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
# ★★★ 計算したいROUGEの種類をここで定義 ★★★
ROUGE_TYPES_TO_CALCULATE = ['rouge1', 'rouge2', 'rougeL']

# --- MeCab Tokenizer ---
class MeCabTokenizer(tokenizers.Tokenizer):
    """MeCabを使って日本語をトークン化するカスタムトークナイザー"""
    def __init__(self):
        self.mecab = MeCab.Tagger("-Owakati")

    def tokenize(self, text: str) -> List[str]:
        return self.mecab.parse(str(text)).strip().split()

def calculate_all_rouge_scores(input_path: str, output_dir: str):
    """
    CSVファイルを読み込み、複数のROUGEスコアを計算して結果のみを新しいCSVファイルに保存する。
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_filename = f"{timestamp}_ROUGEScores_all.csv"
    output_path = os.path.join(output_dir, output_filename)
    os.makedirs(output_dir, exist_ok=True)

    try:
        df = pd.read_csv(input_path)
        print(f"入力ファイル '{input_path}' を読み込みました。")
    except FileNotFoundError:
        print(f"エラー: 入力ファイルが見つかりません: {input_path}")
        return
    
    # 指定した種類のスコアラーを初期化
    scorer = rouge_scorer.RougeScorer(
        rouge_types=ROUGE_TYPES_TO_CALCULATE,
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
        for index, row in tqdm(df_to_process.iterrows(), total=len(df_to_process), desc="ROUGEスコア計算中"):
            row_result = {ID_COLUMN: row[ID_COLUMN]}
            
            try:
                reference_text = str(row[REFERENCE_COLUMN])

                for candidate_col in candidate_columns:
                    candidate_text = row.get(candidate_col)

                    if pd.isna(candidate_text) or str(candidate_text).strip() == '':
                        # 全てのスコアをNoneで埋める
                        for rouge_type in ROUGE_TYPES_TO_CALCULATE:
                            prefix = rouge_type.upper()
                            row_result[f'{prefix}_P_{candidate_col}'] = None
                            row_result[f'{prefix}_R_{candidate_col}'] = None
                            row_result[f'{prefix}_F1_{candidate_col}'] = None
                        continue

                    # 複数のスコアを一度に計算
                    scores = scorer.score(reference_text, str(candidate_text))
                    
                    # 各ROUGEタイプの結果をループで取得
                    for rouge_type, score in scores.items():
                        prefix = rouge_type.upper()
                        row_result[f'{prefix}_P_{candidate_col}'] = score.precision
                        row_result[f'{prefix}_R_{candidate_col}'] = score.recall
                        row_result[f'{prefix}_F1_{candidate_col}'] = score.fmeasure

            except Exception as e:
                print(f"\n行 {index} の処理中にエラーが発生しました: {e}")
                row_result[f'ERROR_NOTE'] = f"ERROR: {e}"

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
    parser = argparse.ArgumentParser(description="CSV内のテキストに対して複数のROUGEスコアを計算します。")
    parser.add_argument("input_file", type=str, help="入力CSVファイルのパス")
    parser.add_argument("output_dir", type=str, help="結果を保存する出力先ディレクトリのパス")
    
    args = parser.parse_args()
    
    calculate_all_rouge_scores(args.input_file, args.output_dir)