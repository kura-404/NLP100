import pandas as pd

# CSVファイルの読み込み
df1 = pd.read_csv("/Users/kuramotomana/Test/成果概要.csv", encoding="utf-8")
df2 = pd.read_csv("/Users/kuramotomana/Test/全課題データ抽出.csv", encoding="utf-8")

# 「課題管理番号」で結合（内部結合：共通するものだけ）
df_merged = pd.merge(df1, df2, on="課題管理番号", how="inner")

# 結果の保存
df_merged.to_csv("merged_output.csv", index=False, encoding="utf-8-sig")

print("✅ 結合が完了しました：merged_output.csv")