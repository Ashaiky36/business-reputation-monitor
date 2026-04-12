#version two for enhanced sentiment analysis

import pandas as pd
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from scipy.special import softmax
from tqdm import tqdm
import ollama
import warnings
import re
warnings.filterwarnings('ignore')

class EnhancedSentimentAnalyzer:
    def __init__(self, use_llm_verification=True, sarcasm_threshold=0.6):
        """
        Initialize the enhanced analyzer with LLM verification for sarcasm
        
        Args:
            use_llm_verification: Whether to use Ollama for sarcasm verification
            sarcasm_threshold: Probability threshold to trigger LLM verification
        """
        print("Loading sentiment model...")
        self.model_name = "cardiffnlp/twitter-roberta-base-sentiment-latest"
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        self.model = AutoModelForSequenceClassification.from_pretrained(self.model_name)
        
        self.use_llm_verification = use_llm_verification
        self.sarcasm_threshold = sarcasm_threshold
        self.sentiment_labels = ['Negative', 'Neutral', 'Positive']
        
        # Cache for LLM results to avoid redundant calls
        self.llm_cache = {}
        
        print(f"✅ Model loaded. LLM Verification: {'ON' if use_llm_verification else 'OFF'}")
        print(f"📊 Sarcasm threshold: {sarcasm_threshold}")
        
    def detect_sarcasm_fast(self, text):
        """
        Fast sarcasm detection using pattern matching and keywords
        Returns a probability score between 0 and 1
        """
        sarcasm_score = 0.0
        text_lower = text.lower()
        
        # Sarcasm indicators - common patterns
        sarcasm_patterns = [
            (r'oh great', 0.7),
            (r'just what i needed', 0.8),
            (r'fantastic.*?wait', 0.7),
            (r'love.*?wait', 0.6),
            (r'brilliant.*?yet again', 0.7),
            (r'(?:so|very) (?:helpful|useful).*?not', 0.6),
            (r'perfect.*?just perfect', 0.8),
            (r'wonderful.*?another', 0.7),
            (r'🙄', 0.9),
            (r'👍.*?not', 0.6),
            (r'excellent.*?fail', 0.7),
        ]
        
        # Check for patterns
        for pattern, weight in sarcasm_patterns:
            if re.search(pattern, text_lower):
                sarcasm_score += weight
        
        # Check for punctuation emphasis (multiple !!! or ???)
        if text.count('!') > 2 or text.count('?') > 2:
            sarcasm_score += 0.3
            
        # Check for contrast (positive word + negative context)
        positive_words = ['love', 'great', 'amazing', 'fantastic', 'perfect', 'wonderful', 'excellent', 'brilliant']
        negative_context = ['wait', 'buggy', 'broken', 'terrible', 'awful', 'horrible', 'useless']
        
        pos_count = sum(word in text_lower for word in positive_words)
        neg_count = sum(word in text_lower for word in negative_context)
        
        if pos_count > 0 and neg_count > 0:
            sarcasm_score += 0.4 * min(pos_count, neg_count)
        
        # Cap at 0.95
        return min(sarcasm_score, 0.95)
    
    def verify_with_llm(self, text, initial_sentiment):
        """
        Use Ollama Mistral to verify if text is sarcastic and get correct sentiment
        """
        # Check cache first
        cache_key = hash(text)
        if cache_key in self.llm_cache:
            return self.llm_cache[cache_key]
        
        prompt = f"""Analyze the following text and determine:
1. Is it sarcastic? (yes/no)
2. What is the TRUE sentiment? (positive/negative/neutral)

Text: "{text}"

Respond in EXACTLY this JSON format:
{{"sarcastic": "yes/no", "true_sentiment": "positive/negative/neutral", "confidence": 0.0-1.0}}

Do not add any other text or explanation."""
        
        try:
            response = ollama.chat(model='mistral', messages=[
                {'role': 'user', 'content': prompt}
            ])
            
            # Parse the response
            result_text = response['message']['content']
            
            # Extract JSON from response
            import json
            # Find JSON in the response
            json_match = re.search(r'\{.*\}', result_text, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
            else:
                # Fallback parsing
                sarcastic = 'yes' if 'sarcastic": "yes' in result_text or 'sarcastic":"yes' in result_text else 'no'
                sentiment_match = re.search(r'true_sentiment["\']?\s*:\s*["\']?(\w+)', result_text)
                true_sentiment = sentiment_match.group(1) if sentiment_match else initial_sentiment.lower()
                confidence_match = re.search(r'confidence["\']?\s*:\s*([0-9.]+)', result_text)
                confidence = float(confidence_match.group(1)) if confidence_match else 0.8
                result = {'sarcastic': sarcastic, 'true_sentiment': true_sentiment, 'confidence': confidence}
            
            # Cache the result
            self.llm_cache[cache_key] = result
            return result
            
        except Exception as e:
            print(f"⚠️ LLM verification failed: {e}")
            return {'sarcastic': 'no', 'true_sentiment': initial_sentiment.lower(), 'confidence': 0.5}
    
    def analyze_sentiment(self, text):
        """
        Analyze sentiment with hybrid sarcasm detection
        """
        # Step 1: Get base sentiment using RoBERTa
        inputs = self.tokenizer(text, return_tensors="pt", truncation=True, max_length=512)
        
        with torch.no_grad():
            outputs = self.model(**inputs)
            probabilities = softmax(outputs.logits.numpy(), axis=1)
        
        sentiment_scores = {
            'Negative': probabilities[0][0],
            'Neutral': probabilities[0][1],
            'Positive': probabilities[0][2]
        }
        
        # Determine initial sentiment
        initial_sentiment = max(sentiment_scores, key=sentiment_scores.get)
        
        # Step 2: Fast sarcasm detection
        fast_sarcasm_score = self.detect_sarcasm_fast(text)
        
        # Step 3: If high probability of sarcasm and LLM verification is enabled, verify
        llm_verified = False
        final_sentiment = initial_sentiment
        is_sarcastic = False
        llm_confidence = 0
        
        if self.use_llm_verification and fast_sarcasm_score >= self.sarcasm_threshold:
            llm_result = self.verify_with_llm(text, initial_sentiment)
            is_sarcastic = llm_result['sarcastic'] == 'yes'
            llm_confidence = llm_result.get('confidence', 0.5)
            
            if is_sarcastic:
                # For sarcastic text, use LLM's sentiment determination
                llm_sentiment = llm_result['true_sentiment'].capitalize()
                if llm_sentiment in ['Positive', 'Negative', 'Neutral']:
                    final_sentiment = llm_sentiment
                    # Adjust scores based on LLM confidence
                    if llm_sentiment == 'Negative':
                        sentiment_scores['Negative'] += llm_confidence * 0.3
                    elif llm_sentiment == 'Positive':
                        sentiment_scores['Positive'] += llm_confidence * 0.3
                    else:
                        sentiment_scores['Neutral'] += llm_confidence * 0.3
                llm_verified = True
        
        # Apply class imbalance handling (weighted for negative)
        sentiment_scores['weighted_negative_score'] = sentiment_scores['Negative'] * 1.5
        
        return {
            'final_sentiment': final_sentiment,
            'sarcasm_detected': is_sarcastic if self.use_llm_verification else (fast_sarcasm_score > 0.6),
            'sarcasm_probability': fast_sarcasm_score,
            'llm_verified': llm_verified,
            'llm_confidence': llm_confidence if llm_verified else 0,
            'sentiment_scores': sentiment_scores,
            'initial_sentiment': initial_sentiment
        }
    
    def analyze_batch(self, texts, batch_size=10):
        """
        Analyze multiple texts with progress bar and optional batching for LLM
        """
        results = []
        llm_calls = 0
        
        for idx, text in enumerate(tqdm(texts, desc="Analyzing sentiments")):
            try:
                result = self.analyze_sentiment(str(text))
                results.append(result)
                if result.get('llm_verified', False):
                    llm_calls += 1
            except Exception as e:
                print(f"\n❌ Error analyzing text at index {idx}: {e}")
                results.append({
                    'final_sentiment': 'Neutral',
                    'sarcasm_detected': False,
                    'sarcasm_probability': 0,
                    'llm_verified': False,
                    'llm_confidence': 0,
                    'sentiment_scores': {'Negative': 0.33, 'Neutral': 0.34, 'Positive': 0.33},
                    'initial_sentiment': 'Neutral'
                })
        
        print(f"\n📊 Analysis complete! LLM verified {llm_calls}/{len(texts)} reviews ({llm_calls/len(texts)*100:.1f}%)")
        return results

def test_with_samples():
    """Test the enhanced analyzer with the sample texts"""
    analyzer = EnhancedSentimentAnalyzer(use_llm_verification=True, sarcasm_threshold=0.3)
    
    test_texts = [
        "This product is absolutely amazing! Best purchase ever!",
        "It's okay, nothing special about it.",
        "Worst experience ever. Would give zero stars if possible.",
        "Oh great, another buggy update. Just what I needed. 🙄",
        "I just love waiting 2 hours for customer service. Fantastic!",
        "Brilliant! The app crashed again. Simply wonderful.",  # Additional sarcastic example
    ]
    
    print("\n" + "="*60)
    print("TESTING ENHANCED SENTIMENT ANALYZER")
    print("="*60)
    
    for text in test_texts:
        result = analyzer.analyze_sentiment(text)
        print(f"\n📝 Text: {text}")
        print(f"🎯 Final Sentiment: {result['final_sentiment']}")
        print(f"😏 Sarcasm: {'✅ YES' if result['sarcasm_detected'] else '❌ NO'} (prob: {result['sarcasm_probability']:.2%})")
        if result['llm_verified']:
            print(f"🤖 LLM Verified: YES (confidence: {result['llm_confidence']:.2%})")
        print(f"📊 Initial Sentiment (without sarcasm check): {result['initial_sentiment']}")
        print(f"📈 Scores - Neg: {result['sentiment_scores']['Negative']:.2f}, Neu: {result['sentiment_scores']['Neutral']:.2f}, Pos: {result['sentiment_scores']['Positive']:.2f}")
        print("-"*40)

def process_csv_file():
    """Process the actual reviews.csv file"""
    print("\n📂 Loading reviews from CSV...")
    df = pd.read_csv('reviews.csv')
    
    # Combine title and content
    df['full_text'] = df['title'].fillna('') + " " + df['content'].fillna('')
    
    # Initialize analyzer
    analyzer = EnhancedSentimentAnalyzer(use_llm_verification=True, sarcasm_threshold=0.3)
    
    # Analyze all reviews
    results = analyzer.analyze_batch(df['full_text'].tolist())
    
    # Add results to dataframe
    df['sentiment'] = [r['final_sentiment'] for r in results]
    df['sarcasm_detected'] = [r['sarcasm_detected'] for r in results]
    df['sarcasm_probability'] = [r['sarcasm_probability'] for r in results]
    df['llm_verified'] = [r['llm_verified'] for r in results]
    df['initial_sentiment'] = [r['initial_sentiment'] for r in results]
    df['sentiment_scores_negative'] = [r['sentiment_scores']['Negative'] for r in results]
    df['sentiment_scores_neutral'] = [r['sentiment_scores']['Neutral'] for r in results]
    df['sentiment_scores_positive'] = [r['sentiment_scores']['Positive'] for r in results]
    
    # Save enriched dataset
    df.to_csv('analyzed_reviews_enhanced.csv', index=False)
    
    # Print comprehensive summary
    print("\n" + "="*60)
    print("ENHANCED SENTIMENT ANALYSIS SUMMARY")
    print("="*60)
    print(f"📊 Total Reviews Analyzed: {len(df)}")
    print(f"\n🎭 Sentiment Distribution:")
    print(df['sentiment'].value_counts())
    print(f"\n😏 Sarcasm Statistics:")
    print(f"   - Reviews with sarcasm: {df['sarcasm_detected'].sum()}")
    print(f"   - Sarcasm percentage: {(df['sarcasm_detected'].sum()/len(df))*100:.1f}%")
    print(f"   - LLM verified sarcasm cases: {df['llm_verified'].sum()}")
    
    # Show sentiment changes after sarcasm detection
    sentiment_changes = df[df['sentiment'] != df['initial_sentiment']]
    if len(sentiment_changes) > 0:
        print(f"\n🔄 Sentiment corrections due to sarcasm detection:")
        for idx, row in sentiment_changes.iterrows():
            print(f"   Review: {row['full_text'][:60]}...")
            print(f"   Changed from {row['initial_sentiment']} → {row['sentiment']} (sarcasm prob: {row['sarcasm_probability']:.2%})")
    
    # Show sarcastic reviews
    sarcastic_reviews = df[df['sarcasm_detected'] == True]
    if len(sarcastic_reviews) > 0:
        print("\n" + "="*60)
        print("🔍 DETECTED SARCASTIC REVIEWS")
        print("="*60)
        for idx, row in sarcastic_reviews.head(5).iterrows():
            print(f"\n📝 Review: {row['full_text'][:100]}...")
            print(f"😏 Sarcasm Probability: {row['sarcasm_probability']:.2%}")
            print(f"🎯 Final Sentiment: {row['sentiment']} (was {row['initial_sentiment']})")
            if row['llm_verified']:
                print(f"🤖 Verified by LLM: YES")
    
    print("\n✅ Analysis complete! Results saved to 'analyzed_reviews_enhanced.csv'")
    
    return df

if __name__ == "__main__":
    print("🚀 ENHANCED SENTIMENT ANALYZER WITH LLM VERIFICATION")
    print("="*60)
    
    # First test with samples
    test_with_samples()
    
    # Ask user if they want to process the CSV
    print("\n" + "="*60)
    response = input("\n📁 Process your reviews.csv file? (yes/no): ").lower()
    if response in ['yes', 'y']:
        process_csv_file()
    else:
        print("✅ Testing complete! You can run process_csv_file() manually when ready.")