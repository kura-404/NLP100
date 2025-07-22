import pandas as pd
from datetime import datetime

# input_file='/Users/kuramotomana/Test/全課題データ抽出.csv_terms_only.csv'

# df=pd.read_csv(input_file)

# values=df['単語'].astype(str)+','

# output_text=''.join(values.tolist())

# timestamp=datetime.now().strftime('%Y%m%d_%H%M%S')
# output_file=f'{timestamp}_output_word.txt'

# with open(output_file,'w',encoding='utf-8') as f:
#     f.write(output_text)


import pandas as pd

# ファイルを1行の文字列として読み込む
with open('Users/kuramotomana/Test/全課題データ抽出.csv_terms_only.csv', 'r', encoding='utf-8') as f:
    content = f.read().strip()

# カンマで分割して単語リストを取得
words = content.split(',')

# 単語の出現回数をカウント（pandasを使う例）
df = pd.Series(words).value_counts()

print(df)