# -*- coding: utf-8 -*-
import MeCab
import unidic
import re

# ===== 可読性スコアの計算式（jreadability準拠） =====
def calc_readability(text, dicdir=None):
    if dicdir is None:
        dicdir = unidic.DICDIR

    tagger = MeCab.Tagger(f"-d {dicdir}")
    tagger.parse("")  # バグ回避のため空文字を最初に投げる

    node = tagger.parseToNode(text)

    total_words = 0
    total_sentences = max(len(re.findall(r'[。！？]', text)), 1)

    kango_count = 0
    wago_count = 0
    verb_count = 0
    particle_count = 0

    while node:
        features = node.feature.split(",")
        if len(features) < 13:
            node = node.next
            continue

        pos = features[0]
        lexical_type = features[12]  # 語種情報（漢・和・外など）

        if node.surface:
            total_words += 1

            # 語種別カウント
            if "漢" in lexical_type:
                kango_count += 1
            elif "和" in lexical_type:
                wago_count += 1

            # 品詞カウント
            if pos == "動詞":
                verb_count += 1
            elif pos == "助詞":
                particle_count += 1

        node = node.next

    # 特徴量計算
    avg_sentence_length = total_words / total_sentences if total_sentences else 0
    kango_ratio = kango_count / total_words if total_words else 0
    wago_ratio = wago_count / total_words if total_words else 0
    verb_ratio = verb_count / total_words if total_words else 0
    particle_ratio = particle_count / total_words if total_words else 0

    # jreadabilityモデルの線形スコア式
    score = (
        -0.056 * avg_sentence_length
        -0.126 * kango_ratio
        -0.042 * wago_ratio
        -0.145 * verb_ratio
        -0.044 * particle_ratio
        + 11.724
    )

    return {
        "score": round(score, 4),
        "avg_sentence_length": avg_sentence_length,
        "kango_ratio": kango_ratio,
        "wago_ratio": wago_ratio,
        "verb_ratio": verb_ratio,
        "particle_ratio": particle_ratio,
        "total_words": total_words,
        "total_sentences": total_sentences,
    }

# ===== テスト =====
if __name__ == "__main__":
    text = "これはMeCab 0.996とUniDic 2.2.0で計算した日本語テキストの可読性スコアです。文が短いと読みやすいとされます。"
    result = calc_readability(text)
    for k, v in result.items():
        print(f"{k}: {v}")