# from openai import OpenAI

# # OpenAIクライアント初期化
# client = OpenAI()

# batches = client.batches.list()
# for b in batches.data:
#     print(f"{b.id}: {b.status}")

# # バッチの状態を再確認
# failed_batch_id = "batch_68240fb8dd64819090493a8e8ca41e56"
# batch = client.batches.retrieve(failed_batch_id)
# print(batch.status)  # → 'failed' のままか？

# # 必要に応じてキャンセル（ただし failed 状態では不要）
# # client.batches.cancel(failed_batch_id) は通常 running 状態のみに有効

from openai import OpenAI
client = OpenAI()

# 組織ごとの現在の利用状況を確認
usage = client.api_usage.retrieve()
print(usage)