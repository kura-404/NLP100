import MeCab
import re
import argparse
import csv

# UniDicの辞書パス（環境に応じて変更）
UNIDIC_PATH = "/Users/kuramotomana/Library/Python/3.9/lib/python/site-packages/unidic/dicdir"

# 文を句点で分割する
def split_sentences(text):
    return [s for s in re.split(r'[。．？！\?!]', text) if s.strip()]

# 形態素解析して、各カテゴリ数をカウント
def analyze_text(text, tagger):
    sentences = split_sentences(text)
    num_sentences = len(sentences)
    total_words = 0
    kango_count = 0
    wago_count = 0
    verb_count = 0
    particle_count = 0

    for sentence in sentences:
        node = tagger.parseToNode(sentence)
        while node:
            if node.stat in (2, 3):  # BOS/EOS
                node = node.next
                continue
            features = node.feature.split(',')
            pos = features[0]
            orig = features[6] if len(features) > 6 else ''
            # 語種情報（UniDicでは第13列目）
            word_type = features[12] if len(features) > 12 else ''

            total_words += 1
            if pos == "動詞":
                verb_count += 1
            elif pos == "助詞":
                particle_count += 1

            if word_type == "漢":
                kango_count += 1
            elif word_type == "和":
                wago_count += 1

            node = node.next

    return {
        "num_sentences": num_sentences,
        "total_words": total_words,
        "kango": kango_count,
        "wago": wago_count,
        "verbs": verb_count,
        "particles": particle_count
    }

# 可読性スコアの算出式（スクリーンショットに基づく）
def compute_readability(counts):
    if counts["num_sentences"] == 0 or counts["total_words"] == 0:
        return None
    avg_words_per_sentence = counts["total_words"] / counts["num_sentences"]
    kango_pct = counts["kango"] / counts["total_words"]
    wago_pct = counts["wago"] / counts["total_words"]
    verb_pct = counts["verbs"] / counts["total_words"]
    particle_pct = counts["particles"] / counts["total_words"]

    score = (
        avg_words_per_sentence * -0.056 +
        kango_pct * -0.126 +
        wago_pct * -0.042 +
        verb_pct * -0.145 +
        particle_pct * -0.044 +
        11.724
    )
    return round(score, 4)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, help="入力CSVファイル")
    parser.add_argument("--text_column", default="text", help="テキストのカラム名")
    parser.add_argument("--output", default="readability_output.csv", help="出力CSVファイル")
    args = parser.parse_args()

    tagger = MeCab.Tagger(f"-d {UNIDIC_PATH}")
    tagger.parse("")  # parseToNode()対策で空パース

    with open(args.input, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    output_rows = []
    for row in rows:
        text = row.get(args.text_column, "")
        counts = analyze_text(text, tagger)
        score = compute_readability(counts)
        row["readability_score"] = score if score is not None else "N/A"
        output_rows.append(row)

    fieldnames = list(output_rows[0].keys())
    with open(args.output, "w", newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(output_rows)

    print(f"✅ 出力完了: {args.output}")

if __name__ == "__main__":
    main()形態素解析辞書 UniDic 2.2.0