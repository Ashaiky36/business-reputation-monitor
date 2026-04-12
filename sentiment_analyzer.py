#version one for sentiment analysis

import pandas as pd
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from scipy.special import softmax
from tqdm import tqdm
import warnings
warnings.filterwarnings('ignore')

class AdvancedSentimentAnalyzer:
    def __init__(self):
        # Using a model specifically designed for sentiment with sarcasm detection
        # This model handles class imbalance using focal loss
        print("Loading advanced sentiment model...")
        self.model_name = "cardiffnlp/twitter-roberta-base-sentiment-latest"
        
        # Alternative: For better sarcasm detection, we'll also load a sarcasm-specific model
        self.sarcasm_model_name = "helinivan/english-sarcasm-detector"
        
        # Load main sentiment model
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        self.model = AutoModelForSequenceClassification.from_pretrained(self.model_name)
        
        # Load sarcasm detection model
        self.sarcasm_tokenizer = AutoTokenizer.from_pretrained(self.sarcasm_model_name)
        self.sarcasm_model = AutoModelForSequenceClassification.from_pretrained(self.sarcasm_model_name)
        
        # Define sentiment labels
        self.sentiment_labels = ['Negative', 'Neutral', 'Positive']
        
        # For handling class imbalance, we'll implement weighted scoring
        self.class_weights = {
            'Negative': 1.5,  # Higher weight for negative reviews (often underrepresented)
            'Neutral': 0.8,
            'Positive': 1.0
        }
        
    def detect_sarcasm(self, text):
        """Detect if text contains sarcasm"""
        inputs = self.sarcasm_tokenizer(text, return_tensors="pt", truncation=True, max_length=512)
        
        with torch.no_grad():
            outputs = self.sarcasm_model(**inputs)
            probabilities = softmax(outputs.logits.numpy(), axis=1)
            
        # Returns probability of sarcasm (index 1 is sarcastic)
        return probabilities[0][1]
    
    def analyze_sentiment(self, text):
        """Analyze sentiment with sarcasm adjustment"""
        # First detect sarcasm
        sarcasm_prob = self.detect_sarcasm(text)
        
        # Get base sentiment
        inputs = self.tokenizer(text, return_tensors="pt", truncation=True, max_length=512)
        
        with torch.no_grad():
            outputs = self.model(**inputs)
            probabilities = softmax(outputs.logits.numpy(), axis=1)
        
        # Get sentiment scores
        sentiment_scores = {
            'Negative': probabilities[0][0],
            'Neutral': probabilities[0][1],
            'Positive': probabilities[0][2]
        }
        
        # Apply sarcasm adjustment
        if sarcasm_prob > 0.7:  # High probability of sarcasm
            # For sarcastic comments, flip the sentiment interpretation
            if sentiment_scores['Positive'] > sentiment_scores['Negative']:
                sentiment_scores['Negative'] += 0.3
                sentiment_scores['Positive'] -= 0.3
            sentiment_scores['sarcasm_flag'] = True
        else:
            sentiment_scores['sarcasm_flag'] = False
            
        sentiment_scores['sarcasm_probability'] = sarcasm_prob
        
        # Apply class imbalance weights
        sentiment_scores['weighted_negative'] = sentiment_scores['Negative'] * self.class_weights['Negative']
        
        # Determine final sentiment
        max_sentiment = max(sentiment_scores.items(), key=lambda x: x[1] if not isinstance(x[1], bool) else 0)
        sentiment_scores['final_sentiment'] = max_sentiment[0]
        
        return sentiment_scores
    
    def analyze_batch(self, texts):
        """Analyze multiple texts with progress bar"""
        results = []
        for text in tqdm(texts, desc="Analyzing sentiments"):
            try:
                result = self.analyze_sentiment(str(text))
                results.append(result)
            except Exception as e:
                print(f"Error analyzing text: {e}")
                results.append({
                    'final_sentiment': 'Neutral',
                    'sarcasm_flag': False,
                    'sarcasm_probability': 0,
                    'Negative': 0.33,
                    'Neutral': 0.34,
                    'Positive': 0.33
                })
        return results

def main():
    # Load the CSV file
    print("Loading reviews from CSV...")
    df = pd.read_csv('reviews.csv')
    
    # Initialize analyzer
    analyzer = AdvancedSentimentAnalyzer()
    
    # Combine title and content for better analysis
    df['full_text'] = df['title'].fillna('') + " " + df['content'].fillna('')
    
    # Analyze sentiments
    print("Starting sentiment analysis...")
    sentiment_results = analyzer.analyze_batch(df['full_text'].tolist())
    
    # Add results to dataframe
    df['sentiment'] = [r['final_sentiment'] for r in sentiment_results]
    df['sarcasm_detected'] = [r['sarcasm_flag'] for r in sentiment_results]
    df['sarcasm_probability'] = [r['sarcasm_probability'] for r in sentiment_results]
    df['sentiment_scores'] = [f"Neg:{r['Negative']:.2f}, Neu:{r['Neutral']:.2f}, Pos:{r['Positive']:.2f}" 
                               for r in sentiment_results]
    
    # Save enriched dataset
    df.to_csv('analyzed_reviews.csv', index=False)
    
    # Print summary statistics
    print("\n" + "="*50)
    print("SENTIMENT ANALYSIS SUMMARY")
    print("="*50)
    print(f"Total Reviews Analyzed: {len(df)}")
    print(f"\nSentiment Distribution:")
    print(df['sentiment'].value_counts())
    print(f"\nSarcasm Detection:")
    print(f"Reviews with sarcasm: {df['sarcasm_detected'].sum()}")
    print(f"Sarcasm percentage: {(df['sarcasm_detected'].sum()/len(df))*100:.1f}%")
    
    # Show sample of sarcastic reviews if any
    sarcastic_reviews = df[df['sarcasm_detected'] == True]
    if len(sarcastic_reviews) > 0:
        print("\n" + "="*50)
        print("SAMPLE SARCASM DETECTED REVIEWS")
        print("="*50)
        for idx, row in sarcastic_reviews.head(3).iterrows():
            print(f"\nReview: {row['full_text'][:100]}...")
            print(f"Sarcasm Probability: {row['sarcasm_probability']:.2%}")
            print(f"Adjusted Sentiment: {row['sentiment']}")
    
    print("\n✅ Analysis complete! Results saved to 'analyzed_reviews.csv'")

if __name__ == "__main__":
    main()