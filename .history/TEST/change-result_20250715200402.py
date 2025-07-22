# -*- coding: utf-8 -*-
import pandas as pd
from datetime import datetime
from openai import OpenAI
from dotenv import load_dotenv
from tqdm import tqdm
import argparse  # 1. argparseをインポート
import os        # 1. osをインポート

# .envからAPIキー読み込み
load_dotenv()

# OpenAIクライアント初期化
client = OpenAI()

# --- この部分は定数として保持 ---
TARGET_COLUMN = "生成された成果概要"
OUTPUT_COLUMN = "改良プロンプトによる書き換え"
SYSTEM_PROMPT = """
以下の研究概要を指示に従って書き換えてください。
前置きのコメントや説明は不要です。
書き換えた文章だけを出力してください。
与えられたテキストに含まれる情報を削除・追加せず、内容を正確に保持したまま、文章の構造を大きく崩さずに、自然な日本語でわかりやすく書き換えてください。
専門用語が出てきた場合は、必要に応じて括弧などで短い説明を加え、高校生でも意味が理解できるようにしてください。
専門用語の言い換えも可能ですが、意味が変わらないよう注意し、説明が難しい場合はそのまま使って簡単な補足を添えてください。
特に医療用語に関しては丁寧に説明・補足をしてください。
また、文章を堅苦しくしすぎず、親しみやすい言い回しを心がけてください。
テキストの正誤については判断せず、与えられた情報を忠実に取り扱ってください。
"""

def main(input_file, output_dir):
    """メインの処理を実行する関数"""
    
    # 出力ファイル名（タイムスタンプ付き）を生成
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_filename = f"rewritten_output_{timestamp}.csv"
    # 3. 出力ディレクトリとファイル名を結合して完全なパスを作成
    output_file_path = os.path.join(output_dir, output_filename)
    
    # ディレクトリが存在しない場合は作成
    os.makedirs(output_dir, exist_ok=True)

    # CSV読み込み
    try:
        df = pd.read_csv(input_file)
    except FileNotFoundError:
        print(f"エラー: 入力ファイルが見つかりません: {input_file}")
        return # 関数を終了

    # 新しい列を作成し、書き換え結果を格納
    rewritten_list = []

    for i, row in tqdm(df.iterrows(), total=df.shape[0], desc="テキスト書き換え中"):
        original_text = row.get(TARGET_COLUMN, "")
        if pd.isna(original_text) or original_text.strip() == "":
            rewritten_list.append("")
            continue

        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": original_text}
                ],
                temperature=0.5
            )
            rewritten_text = response.choices[0].message.content.strip()
        except Exception as e:
            rewritten_text = f"エラー発生: {e}"

        rewritten_list.append(rewritten_text)

    # 新しい列を追加
    df[OUTPUT_COLUMN] = rewritten_list

    # 新しいCSVとして保存
    df.to_csv(output_file_path, index=False, encoding="utf-8-sig")

    print(f"\n完了：{output_file_path} に保存されました。")

# --- ここからがスクリプト実行時のエントリーポイント ---
if __name__ == "__main__":
    # 2. コマンドライン引数のパーサーを作成
    parser = argparse.ArgumentParser(description="OpenAI APIを使ってCSVファイル内のテキストを書き換えます。")
    
    # 2-1. 受け取る引数を定義
    parser.add_argument("input_file", type=str, help="入力CSVファイルのパス")
    parser.add_argument("output_dir", type=str, help="出力先ディレクトリのパス")
    
    # 2-2. コマンドライン引数を解析
    args = parser.parse_args()
    
    # 3. 解析した引数をmain関数に渡して実行
    main(args.input_file, args.output_dir)