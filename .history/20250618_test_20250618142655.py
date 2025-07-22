import MeCab
import os

# ユーザー辞書のパス（UniDic-MeCab 2.1.2 modelのパスに変更）
dic_dir = "/Users/kuramotomana/Desktop/unidic-mecab-2.1.2_model" # 解凍したディレクトリ名に合わせてください

tagger = MeCab.Tagger(f"-d {dic_dir}")
tagger.parse("")

def analyze(text):
    node = tagger.parseToNode(text)

    total_words = 0
    sentences = text.count('。') + text.count('？') + text.count('！')
    if sentences == 0:
        sentences = 1

    kango = 0
    wago = 0
    verbs = 0
    auxiliary_verbs = 0

    print("--- MeCab Analysis Details ---")
    while node:
        if node.stat in (2, 3):
            node = node.next
            continue

        total_words += 1
        features = node.feature.split(',')
        word = node.surface

        pos = features[0] if len(features) > 0 else ''
        word_type = features[12] if len(features) > 12 else '' # 語種（UniDic 特有）

        print(f"Word: {word}, POS: {pos}, WordType (features[12]): '{word_type}'")

        # ★★★ ここを修正します ★★★
        if word_type == '漢':
            kango += 1
        elif word_type == '和':
            wago += 1
        elif word_type == '固' or word_type == '外': # 固有名詞と外来語を漢語に含める
            kango += 1
        # '記号'などはカウントしない（jReadability.netの漢語+和語が総語数と一致しているため、
        # 記号はそもそも総語数に含まれていないか、他の分類に吸収されている可能性もあるが、
        # スクリーンショットの「品詞」内訳では「記号」が別でカウントされているので、
        # 今回は「記号」は語種カウントから除外します。）

        if pos == '動詞':
            verbs += 1
        elif pos == '助動詞':
            auxiliary_verbs += 1

        node = node.next
    print("--- End of Analysis Details ---")

    mean_words_per_sentence = total_words / sentences
    percent = lambda x: (x / total_words * 100) if total_words > 0 else 0

    readability = (
        mean_words_per_sentence * -0.056 +
        percent(kango) * -0.126 +
        percent(wago) * -0.042 +
        percent(verbs) * -0.145 +
        percent(auxiliary_verbs) * -0.044 +
        11.724
    )

    return {
        "readability_score": readability,
        "mean_words_per_sentence": mean_words_per_sentence,
        "percent_kango": percent(kango),
        "percent_wago": percent(wago),
        "percent_verbs": percent(verbs),
        "percent_auxiliary_verbs": percent(auxiliary_verbs),
        "total_words": total_words,
        "sentences": sentences
    }

if __name__ == "__main__":
    text = "日本語の文章の読みやすさを評価するために、このスクリプトを使用します。"
    result = analyze(text)
    for key, value in result.items():
        print(f"{key}: {value:.3f}" if isinstance(value, float) else f"{key}: {value}")