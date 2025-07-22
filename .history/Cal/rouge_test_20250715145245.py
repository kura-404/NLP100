import MeCab
from rouge_score import rouge_scorer, tokenizers
from typing import List

# MeCabの初期化（エラーハンドリングなし）
# -r オプションのパスはユーザーの環境に合わせてください。
# 多くの場合、-Owakati だけで動作します。
# MeCabの初期化に失敗した場合、ここで例外が発生しプログラムは停止します。
# mecab_tagger = MeCab.Tagger("-r /opt/homebrew/etc/mecabrc -Owakati")
# あるいは、多くの場合こちらで十分かもしれません:
mecab_tagger = MeCab.Tagger("-Owakati")


# rouge_scoreが期待するトークナイザーインターフェースを持つカスタムクラス
# rouge_score.tokenizers.Tokenizer を継承し、tokenize(text) メソッドを実装する
class MeCabTokenizer(tokenizers.Tokenizer):
    """MeCabを使って日本語をトークン化するカスタムトークナイザー"""

    def tokenize(self, text: str) -> List[str]:
        """
        入力テキストをMeCabで分かち書きし、単語のリストを返します。
        """
        # mecab_tagger はこのクラスがインスタンス化される前に
        # グローバルで初期化されていることを前提とします。

        # MeCabのparse結果は最後に改行が含まれることがあるのでstrip()
        wakati_str = mecab_tagger.parse(text).strip()

        # スペースで分割して単語のリストにする
        return wakati_str.split()

# スコア計算器を初期化
# rouge_scorer.RougeScorer にカスタムトークナイザーのインスタンスを渡す
# use_stemmer=False: ステミングを行わない設定。日本語では不要。
# tokenizer=MeCabTokenizer(): 作成したMeCabTokenizerのインスタンスを渡す
scorer = rouge_scorer.RougeScorer(
    rouge_types=['rougeL'],
    use_stemmer=False,
    tokenizer=MeCabTokenizer()
)

# 比較対象のテキスト（MeCabで前処理する前の元の文字列）
# reference_text = "こんにちは，私の今日の朝食は，なったまご飯です．"
# prediction_text = "こんにちは，僕の今日の朝ごはんは，トーストです．"
reference_text = "こんにちわに"
prediction_text = "こんにちわに"
# reference_text = """76歳男性、2023年1月4日入院、1月23日退院。アレルギーなし。退院時診断はSIADH（軽快）と肺小細胞癌（不変）。主訴は食欲不振と倦怠感。入院前1週間、倦怠感と水様便、食欲不振、微熱、体重減少を認めた。既往歴に高血圧症。喫煙歴あり。家族歴に大腸癌。入院時、低Na血症、左肺野に腫瘍影、肝転移を認めた。気管支鏡検査で肺小細胞癌と診断。化学療法は行わず、施設入所の方針。退院時、状態安定。施設で対症療法と緩和治療を継続。"""
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

# スコア計算
score_results = scorer.score(reference_text, prediction_text)

# rougeLの結果を取得
score = score_results['rougeL']


# 結果を出力
temp_tokenizer = MeCabTokenizer()
print("Reference (tokens by MeCabTokenizer):", temp_tokenizer.tokenize(reference_text))
print("Prediction (tokens by MeCabTokenizer):", temp_tokenizer.tokenize(prediction_text))
print(f"\nROUGE-L Score:")
print(f"  Precision: {score.precision:.3f}")
print(f"  Recall:    {score.recall:.3f}")
print(f"  F1 Score:  {score.fmeasure:.3f}")