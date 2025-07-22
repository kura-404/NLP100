import MeCab
from nltk.translate.bleu_score import sentence_bleu, SmoothingFunction
from typing import List

# MeCabの初期化
mecab_tagger = MeCab.Tagger("-Owakati")
# mecab_tagger = MeCab.Tagger("-Owakati -d /opt/homebrew/lib/mecab/dic/ipadic -u /Users/himi/work/sum/data/MANBYO_202106.dic")

# トークナイザークラス
class MeCabTokenizer:
    def tokenize(self, text: str) -> List[str]:
        wakati_str = mecab_tagger.parse(text).strip()
        return wakati_str.split()

# インスタンス化
tokenizer = MeCabTokenizer()

# 比較対象のテキスト（MeCabで前処理する前の元の文字列）
reference_text = "こんにちは，私の今日の朝食は，なったまご飯です．"
prediction_text = "こんにちは，僕の今日の朝ごはんは，トーストです．"
prediction_text = "こんにちは，なったまご飯．私の朝食の今日はです，"
# reference_text = """
# # 肺小細胞癌
# # 低Na血症
# 　１週間前から倦怠感と水様便（１日2-4回）が出現、食欲不振あり。体重が3kg減少あり。食欲不振と倦怠感を主訴に外来受診した。
# 　採血でNa 118と低Na血症を認め、同日入院の上で電解質補正を行った。
# 　Naは安定し、嘔気・水曜便は改善した。入院時に左肺野の腫瘍の精査目的に気管支鏡検査を行った。病理診断から肺小細胞癌の診断、肝転移もあり。
# 　本人・家族と相談で、化学療法は行わない方針となった。
# 　長期の入院により独歩で帰宅は困難であり、1/23に施設に退院となった。
# 　今後は、施設でBSCの方針。
# """

# prediction_text = """
# 【症例】76y.o., M
# 【病名】肺小細胞癌、SIADH
# 【既往歴】HT
# 【家族歴】兄：60歳で大腸Ca
# 【生活歴】喫煙：40本X56年、飲酒なし、妻と二人暮らし→施設
# 【内服薬】Ca blocker
# 【現病歴】2022/12/28より倦怠感、水様性下痢、悪心、食欲不振。-3kgの体重減少あり。2023/1/4入院となる。
# 【検査結果】入院時BP 86/50mmHg, R.R. 20/min, 皮膚・口腔内の乾燥あり。ばち指あり
# 採血・尿：AST 43U/L、ALT 78U/L、γ-GT
# """

# トークナイズ
ref_tokens = [tokenizer.tokenize(reference_text)]
cand_tokens = tokenizer.tokenize(prediction_text)

# BLEUスコアの計算（smoothing を使わないと 0 になることがある）
score = sentence_bleu(ref_tokens, cand_tokens, smoothing_function=SmoothingFunction().method1)

# 出力
print("Reference (tokens):", ref_tokens[0])
print("Prediction (tokens):", cand_tokens)
print(f"\nBLEUスコア: {score:.4f}")
