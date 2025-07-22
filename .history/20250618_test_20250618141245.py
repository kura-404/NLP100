import MeCab
import os

# ユーザー辞書のパス（フルパスで指定）
dic_dir = "/Users/kuramotomana/Desktop/unidic-csj-2.2.0"

# MeCab Tagger に -d オプションで辞書指定
tagger = MeCab.Tagger(f"-d {dic_dir}")
tagger.parse("")  # BOS/EOSバグ回避

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

    print("--- MeCab Analysis Details ---") # デバッグ情報開始
    while node:
        if node.stat in (2, 3):  # BOS/EOS
            node = node.next
            continue

        total_words += 1
        features = node.feature.split(',')
        word = node.surface # 単語そのもの

        pos = features[0] if len(features) > 0 else ''
        
        # ★★★ ここを修正しました！ features[13] から features[12] へ ★★★
        word_type = features[12] if len(features) > 12 else ''  # 語種（UniDic 特有）

        print(f"Word: {word}, POS: {pos}, WordType (features[12]): '{word_type}'") # デバッグ出力も変更

        if word_type == '漢':
            kango += 1
        elif word_type == '和':
            wago += 1
        # '外' (外来語) は漢語・和語には含めない

        if pos == '動詞':
            verbs += 1
        elif pos == '助動詞':
            auxiliary_verbs += 1

        node = node.next
    print("--- End of Analysis Details ---") # デバッグ情報終了

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