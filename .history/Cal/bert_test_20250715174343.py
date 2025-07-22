from bert_score import score
from transformers import AutoModel, AutoTokenizer
import torch

# 使用するBERTモデルの名前 (Hugging Face HubでのモデルID)
model_name = 'tohoku-nlp/bert-base-japanese-v3'


candidates = ["こんにちは，私の今日の朝食は，なったまご飯です．"]
references = ["こんにちは，僕の今日の朝ごはんは，トーストですよ〜．"]
candidates = ["""
本研究は、糖尿病患者の腎症（腎臓の病気）が進行するかどうかを予測する新しい血液中の指標「マイクロRNA-XYZ」の有効性を調べるために、複数の医療機関が協力して行った前向き観察研究です。令和4年度には、全国の糖尿病治療を行う10施設で合計500人の糖尿病患者を登録し、基本情報の収集と血液サンプルの採取を完了しました。マイクロRNA-XYZの測定は専門の検査機関でRT-qPCR法（遺伝子の量を正確に測る技術）を用いて行い、腎臓の機能を示す指標（推定糸球体濾過量：eGFR、尿中のアルブミン排泄量）との関係を分析しました。その結果、マイクロRNA-XYZの血中濃度は腎症の初期段階で有意に高く（p<0.01）、この濃度が腎機能の悪化を予測する独立した因子であることが多変量解析（複数の要因を同時に分析する方法）で明らかになりました（ハザード比2.5、95％信頼区間1.7-3.8）。さらに、追跡調査期間中に腎症が進行した患者では、調査開始時のマイクロRNA-XYZの濃度が有意に高いことも確認されました。これらの結果は、マイクロRNA-XYZが糖尿病性腎症の早期発見および進行予測に役立つバイオマーカー（病気の状態を示す指標）となる可能性を示しています。今後は、本研究のデータを基に、より大規模な検証試験や診断キットの開発に向けた連携を進める予定です。
"""]

references = ["""
【症例】76y.o., M
【病名】肺小細胞癌、SIADH
【既往歴】HT
【家族歴】兄：60歳で大腸Ca
【生活歴】喫煙：40本X56年、飲酒なし、妻と二人暮らし→施設
【内服薬】Ca blocker
【現病歴】2022/12/28より倦怠感、水様性下痢、悪心、食欲不振。-3kgの体重減少あり。2023/1/4入院となる。
【検査結果】入院時BP 86/50mmHg, R.R. 20/min, 皮膚・口腔内の乾燥あり。ばち指あり
採血・尿：AST 43U/L、ALT 78U/L、γ-GT
"""]

# モデルを指定する場合には，num_layersを手動で指定する必要あり
P, R, F1 = score(candidates, references, model_type=model_name, num_layers=12, verbose=True)

print(f"Precision: {P.mean().item():.4f}")
print(f"Recall:    {R.mean().item():.4f}")
print(f"F1 Score:  {F1.mean().item():.4f}")
