import pandas as pd
from datetime import datetime

input_file=''

df=pd.read_csv(input_file)

values=df['単語'].astype(str)+','

output_text=''.join(values.tolist())

timestamp=datetime.now().strftime('%Y%m%d_%H%M%S')
output_file=f'{timestamp}_output_word.txt'

with open(output_file,'w',encoding='utf-8') as f:
    f.write(output_text)