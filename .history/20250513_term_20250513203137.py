from tqdm import tqdm
from datetime import datetime

# ファイル読み込みとリスト作成
print("📂 ファイル読み込み中...")
FILE_NAME = "/Users/kuramotomana/Test/成果概要.csv"
df = pd.read_csv(FILE_NAME, encoding='utf-8-sig')
research_abstracts = df['成果概要（日本語）'].dropna().drop_duplicates().tolist()

print(f"🔢 レコード数（重複・欠損除外）: {len(research_abstracts)}")

# チャンク分割
CHUNK_SIZE = 200
chunks = [research_abstracts[i:i + CHUNK_SIZE] for i in range(0, len(research_abstracts), CHUNK_SIZE)]
total_batches = len(chunks)
print(f"📦 チャンク数: {total_batches}（1チャンク ≒ {CHUNK_SIZE}件）")

# request_data作成＆送信
print("🚀 バッチ送信開始")
os.makedirs("data", exist_ok=True)
with tqdm(total=total_batches, desc="送信中", unit="チャンク") as pbar:
    for i, chunk in enumerate(chunks):
        joined_chunk = "\n".join(chunk)
        request_data = [{
            "custom_id": f"request-{i}",
            "method": "POST",
            "url": "/v1/chat/completions",
            "body": {
                "model": "gpt-4.1-mini",
                "messages": [
                    {
                        "role": "system",
                        "content": "次のテキストから用語を抽出してください。出力は抽出した用語のみ、空白区切りで記述してください。"
                    },
                    {
                        "role": "user",
                        "content": joined_chunk
                    }
                ],
                "max_tokens": 2000
            }
        }]
        jsonl_path = f"data/batch_{i}.jsonl"
        write_jsonl(jsonl_path, request_data)
        batch_input_file = client.files.create(file=open(jsonl_path, "rb"), purpose="batch")
        batch_metadata = client.batches.create(
            input_file_id=batch_input_file.id,
            endpoint="/v1/chat/completions",
            completion_window="24h",
            metadata={"description": "chunk-based-batch"}
        )
        with open('request_input_id.csv', 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([jsonl_path, batch_metadata.id, batch_input_file.id])
        confirm_batch_status(batch_metadata, batch_input_file.id)
        pbar.update(1)

# 出力取得
print("📥 出力取得中...")
df_request_batch = pd.read_csv("request_input_id.csv", header=None, names=["input_file", "batch_id", "input_file_id"])
batche_ids = df_request_batch['batch_id'].tolist()

yomi_outputs = []
with tqdm(total=len(batche_ids), desc="取得中", unit="バッチ") as pbar:
    for batch_count, ids in enumerate(batche_ids):
        batches_information = client.batches.retrieve(ids)
        if batches_information.status == "completed" and batches_information.output_file_id is not None:
            file_response = client.files.content(batches_information.output_file_id)
            output = [json.loads(i) for i in file_response.text.strip().split('\n')]
            for o in output:
                yomi_output = o['response']['body']['choices'][0]['message']['content']
                yomi_outputs.append(yomi_output)
        pbar.update(1)

# CSV出力
print("💾 用語リストを出力中...")
terms_list = []
for row in yomi_outputs:
    terms_list.extend(row.strip().split())

timestamp = datetime.now().strftime("%Y%m%d_%H%M")
base_name = os.path.splitext(os.path.basename(FILE_NAME))[0]
output_filename = f"{timestamp}_{base_name}_terms_only.csv"
with open(output_filename, 'w', encoding='utf-8', newline='') as f:
    f.write(','.join(terms_list))

print(f"✅ 出力完了: {output_filename}（語数: {len(terms_list):,}）")