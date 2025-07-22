import pandas as pd
from datetime import datetime

# input_file='/Users/kuramotomana/Test/全課題データ抽出.csv_terms_only.csv'

import pandas as pd
from datetime import datetime

input_file = 'your_input_file.csv'  # ← ファイル名を適宜変更

# 1行をテキストとして読み込んでカンマで分割
with open(input_file, 'r', encoding='utf-8') as f:
    content = f.read().strip()

words = content.split(',')  # 単語のリスト

# カンマ付きの文字列を作成（末尾にもカンマがつく）
values = [word + ',' for word in words]

# リストを結合
output_text = ''.join(values)

# タイムスタンプ付きファイル名で出力
timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
output_file = f'{timestamp}_output_word.txt'

with open(output_file, 'w', encoding='utf-8') as f:
    f.write(output_text)