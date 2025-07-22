#厚労科研を年度ごとにスプリット
import pandas as pd
import os

input_file="/Users/kuramotomana/Test/20250519-厚労科研.csv"

output_dir="split_by_year"
os.makedirs(output_dir,exist_ok=True)

df=pd.read_csv(input_file)

if "研究年度" in df.columns:
    for year,group in df.groupby("研究年度"):
        output_path=os.path.join(output_dir,f"年度_{year}.csv")
        group.to_csv(output_path,index=False,encoding="utf-8-sig")
    print(f"保存完了:{output_dir}フォルダ内に年度別ファイルが作成されました")
else:
    print("エラー:「研究年度」列が見つかりませんでした。")