import pandas as pd
from datetime import datetime

input_file='/Users/kuramotomana/Test/20250521_0052_20250520fillter_terms_only.csv'

# 1行のテキストを読み込み、単語ごとに分割
with open(input_file, 'r', encoding='utf-8') as f:
    content = f.read().strip()

words = content.split(',')  # 単語リスト

# DataFrameにして出現頻度をカウント
df = pd.Series(words).value_counts().reset_index()
df.columns = ['単語', '頻度']

# タイムスタンプ付きファイル名でCSVとして保存
timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
output_file = f'{timestamp}_word_count.csv'

df.to_csv(output_file, index=False, encoding='utf-8')

print(f"出力ファイル: {output_file}")