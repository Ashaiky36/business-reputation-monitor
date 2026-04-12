from sentiment_analyzer import AdvancedSentimentAnalyzer

analyzer = AdvancedSentimentAnalyzer()

test_texts = [
    "This product is absolutely amazing! Best purchase ever!",
    "It's okay, nothing special about it.",
    "Worst experience ever. Would give zero stars if possible.",
    "Oh great, another buggy update. Just what I needed. 🙄",  # Sarcastic
    "I just love waiting 2 hours for customer service. Fantastic!",  # Sarcastic
]

for text in test_texts:
    result = analyzer.analyze_sentiment(text)
    print(f"\nText: {text}")
    print(f"Sentiment: {result['final_sentiment']}")
    print(f"Sarcasm: {'YES' if result['sarcasm_flag'] else 'NO'} ({result['sarcasm_probability']:.2%})")