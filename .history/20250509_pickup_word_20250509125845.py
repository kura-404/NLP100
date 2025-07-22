import pandas as pd
from datetime import datetime

input_file='/Users/kuramotomana/Test/word_frequencies.csv'

df=pd.read_csv(input_file)

values=df['単語'].astype(str)+','

output_text=''.join(values.tolist())

timestamp_datetime.now().strftime('%Y%m%d_%H%M%S')
output_file=f.'{timestamp}_output_word.txt'

