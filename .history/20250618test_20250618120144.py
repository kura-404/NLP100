from jreadability import compute_readability

# "Good morning! The weather is nice today."
text = 'おはようございます！今日は天気がいいですね。' 

score = compute_readability(text)

print(score) # 6.438000000000001