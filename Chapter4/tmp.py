import spacy

nlp = spacy.load("ja_ginza")  # ginza 5.1.2 ではこれは使えます
doc = nlp("彼は毎朝コーヒーを飲みます。")

for token in doc:
    print(token.text, token.lemma_, token.pos_, token.dep_, token.head.text)