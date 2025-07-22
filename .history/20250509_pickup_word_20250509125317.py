import pandas as pd
from datetime import datetime

# 元のCSVファイルのパス
input_file = '/Users/kuramotomana/Test/word_frequencies.csv'

# CSVファイルを読み込む
df = pd.read_csv(input_file)

# A列のみを抽出（列名が"A"であることが前提）
df_a = df[['単語']].astype(str)+','

# 現在の日時を取得してファイル名に使用
timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
output_file = f'{timestamp}_output_Acol.csv'

# 新しいCSVファイルとして保存
df_a.to_csv(output_file, index=False, sep=',')

print(f"A列のみを抽出して保存しました: {output_file}")