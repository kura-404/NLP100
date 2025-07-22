# test_mecab.py
from fugashi import Tagger
from jreadability import compute_readability

tagger = Tagger()
text = "これはMeCab 0.996で動いています。"
score = compute_readability(text, tagger)
print(f"可読性スコア: {score}")