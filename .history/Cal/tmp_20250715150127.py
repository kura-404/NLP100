from transformers import AutoTokenizer

# この一行を実行すると、'tohoku-nlp/bert-base-japanese-v3'が
# 自動的にダウンロードされ、キャッシュディレクトリに保存されます。
tokenizer = AutoTokenizer.from_pretrained('tohoku-nlp/bert-base-japanese-v3')

print("モデルのダウンロードとキャッシュが完了しました。")