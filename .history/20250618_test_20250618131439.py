# test_mecab.py
from fugashi import Tagger
from jreadability import compute_readability

tagger = Tagger()
text = "現在、切除不能・術後再発胆道癌に対する標準治療はゲムシタビン+シスプラチン療法である。わが国ではS-1を加えた3剤をkey drugとして治療が組み立てられているが、十分な治療成績は得られておらず、予後向上のためには新たな治療法の開発が求められている。本研究は切除不能・術後再発胆道癌に対するFOLFIRINOX療法の適応拡大を目指して、先進医療制度下に有効性および安全性を評価する多施設共同非盲検非対照第2相試験である。主要評価項目は無増悪生存期間、副次評価項目は全生存期間、抗腫瘍効果(奏効率・病勢制御率)、安全性で、35症例を対象とする。本研究でFOLFIRINOX療法が有望と判断された場合、薬事承認および保険適応を得ることを目的として、ゲムシタビン+シスプラチン療法との比較試験を検討する。"
score = compute_readability(text, tagger)
print(f"可読性スコア: {score}")