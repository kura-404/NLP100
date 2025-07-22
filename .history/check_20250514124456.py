・

from openai import OpenAI
client = OpenAI()

# 組織ごとの現在の利用状況を確認
usage = client.api_usage.retrieve()
print(usage)