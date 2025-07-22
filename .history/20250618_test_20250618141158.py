import MeCab
import os

dic_dir = "/Users/kuramotomana/Desktop/unidic-csj-2.2.0"
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

        # ここで features リスト全体と len(features) を出力して確認
        print(f"Word: {word}")
        print(f"  Full Feature String: {node.feature}")
        print(f"  Features List (split by comma): {features}")
        print(f"  Length of features list: {len(features)}")

        # 語種フィールドを直接見て、正しいインデックスを特定
        # 例として、もし features[13] が "*" で、features[14] が "漢" や "和" だった場合、
        # word_type_index を 14 に変更する必要がある
        word_type_index = 13 # デフォルトは13のまま

        # ここで、features[13]以外のインデックスも確認し、
        # 実際に語種の情報が入っているインデックスを見つける必要があります。
        # 例えば、features の中をループして '漢' や '和' を探すか、
        # UniDicのドキュメントで正確なフィールド定義を確認します。
        
        # もし features[13] が期待通りでない場合、
        # 別の場所にある「語種」を示すフィールドを探す必要があります。
        # UniDicのMeCab出力フォーマットは非常に長く、バージョンによって微調整がある可能性があります。

        word_type = features[word_type_index] if len(features) > word_type_index else ''

        print(f"  POS (features[0]): '{pos}'")
        print(f"  WordType (features[{word_type_index}]): '{word_type}'") # 正しいインデックスで再確認

        if word_type == '漢':
            kango += 1
        elif word_type == '和':
            wago += 1
        # '外' (外来語) をカウントしないのは、jReadability.netの漢語・和語の割合に合わせるため。

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