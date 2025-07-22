from openai import OpenAI

# OpenAIクライアント初期化
client = OpenAI()

# 全バッチの一覧を取得
batches = client.batches.list()

# ステータスを出力
for b in batches.data:
    print(f"{b.id}: {b.status} (created at {b.created_at})")