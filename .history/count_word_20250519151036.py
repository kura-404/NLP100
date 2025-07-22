import csv
from collections import Counter
from datetime import datetime

# 入力ファイルパス
input_file_path = "/Users/kuramotomana/Test/yomi_outputs.csv"

# 現在の時刻を取得してファイル名に使用
timestamp = datetime.now().strftime("%Y%m%d_%H%M")
output_file_path = f"/Users/kuramotomana/Test/{timestamp}_word_frequencies.csv"

# 単語の頻度カウント用
word_counter = Counter()
total_word_count = 0  # 重複を含めた単語数

# CSV読み込み
with open(input_file_path, newline='', encoding='utf-8') as csvfile:
    reader = csv.reader(csvfile)
    for row in reader:
        for cell in row:
            if '\n' in cell:
                lines = [line.strip() for line in cell.strip().split('\n') if line.strip()]
                word_counter.update(lines)
                total_word_count += len(lines)

# 結果出力（ターミナル用）
print("▼ 単語ごとの頻度:")
for word, count in word_counter.most_common():
    print(f"{word}: {count}")

print(f"\n検出されたユニーク単語数: {len(word_counter)}")
print(f"重複を含む総単語数: {total_word_count}")

# 結果をCSVに書き込み
with open(output_file_path, mode='w', newline='', encoding='utf-8') as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(["単語", "頻度"])  # ヘッダー
    for word, count in word_counter.most_common():
        writer.writerow([word, count])

print(f"\n✅ 結果を '{output_file_path}' に保存しました。")