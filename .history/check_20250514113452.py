from openai import OpenAI

# OpenAIクライアント初期化
client = OpenAI()

batches = client.batches.list()
for b in batches.data:
    print(f"{b.id}: {b.status}")