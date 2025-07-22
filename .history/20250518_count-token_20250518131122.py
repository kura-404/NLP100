#csvファイルを読み込んで8000トークンごとに1リストにしてリストが幾つできるかを確認するコード
import csv
import tiktoken

csv_file_path_"/Users/kuramotomana/Test/成果概要.csv"
target_column_name="成果概要（日本語）"
max_tokens_per_list=8000

encoding_tiktoken.get_encoding("cl100k_base")

def count_tokens(text:str)->int:
    return len(encoding.encode(text))

unique_values=set()
with open(csv_file_path,newline='',encoding="utf-8") as csvfile:
    reader=csv.DictReader(csvfile)
    for row in reader:
        if target_column_name in row:
            value=row[target_column_name].strip()
            if value:
                unique_values.add(value)

lists=[]
current_list=[]
current_tokens=0

for value in sorted(unique_values):
    tokens=count_tokens(value)
    if current_tokens(value)
    