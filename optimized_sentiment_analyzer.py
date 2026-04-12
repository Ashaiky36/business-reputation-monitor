import pandas as pd
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from scipy.special import softmax
from tqdm import tqdm
import ollama
import json
import re
import time
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

class OptimizedSentimentAnalyzer:
    def __init__(self, sarcasm_threshold=0.3, batch_llm_size=5):
        """
        Optimized analyzer with batching and pre-filtering
        
        Args:
            sarcasm_threshold: Threshold for LLM verification (optimized at 0.3)
            batch_llm_size: Number of reviews to send in each LLM batch
        """
        print("🚀 Loading optimized sentiment model...")
        self.model_name = "cardiffnlp/twitter-roberta-base-sentiment-latest"
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        self.model = AutoModelForSequenceClassification.from_pretrained(self.model_name)
        
        self.sarcasm_threshold = sarcasm_threshold
        self.batch_llm_size = batch_llm_size
        self.sentiment_labels = ['Negative', 'Neutral', 'Positive']
        
        # Statistics tracking
        self.stats = {
            'total_reviews': 0,
            'fast_checks': 0,
            'llm_calls': 0,
            'llm_batches': 0,
            'time_fast_detection': 0,
            'time_llm_verification': 0
        }
        
        print(f"✅ Model loaded. LLM Threshold: {sarcasm_threshold}")
        print(f"📦 Batch size for LLM: {batch_llm_size}")
        
    def detect_sarcasm_fast(self, text):
        """
        Optimized fast sarcasm detection with comprehensive patterns
        """
        sarcasm_score = 0.0
        text_lower = text.lower()
        
        # Expanded sarcasm patterns
        sarcasm_patterns = [
            (r'oh great', 0.7), (r'just what i needed', 0.8), (r'fantastic.*?wait', 0.7),
            (r'love.*?wait', 0.6), (r'brilliant.*?yet again', 0.7), (r'(?:so|very) (?:helpful|useful).*?not', 0.6),
            (r'perfect.*?just perfect', 0.8), (r'wonderful.*?another', 0.7), (r'🙄', 0.9),
            (r'👍.*?not', 0.6), (r'excellent.*?fail', 0.7), (r'yeah right', 0.7),
            (r'sure you did', 0.7), (r'as if', 0.6), (r'whatever', 0.5),
            (r'be careful', 0.4), (r'warning', 0.3), (r'plebs', 0.8),  # Added based on your data
            (r'is a joke', 0.7),  # "Apple is a joke"
        ]
        
        # Check patterns
        for pattern, weight in sarcasm_patterns:
            if re.search(pattern, text_lower):
                sarcasm_score += weight
        
        # Punctuation emphasis
        if text.count('!') > 2 or text.count('?') > 2:
            sarcasm_score += 0.3
            
        # Contrast detection (positive words + negative context)
        positive_words = ['love', 'great', 'amazing', 'fantastic', 'perfect', 'wonderful', 'excellent', 'brilliant', 'good']
        negative_context = ['wait', 'buggy', 'broken', 'terrible', 'awful', 'horrible', 'useless', 'joke', 'careful']
        
        pos_count = sum(word in text_lower for word in positive_words)
        neg_count = sum(word in text_lower for word in negative_context)
        
        if pos_count > 0 and neg_count > 0:
            sarcasm_score += 0.4 * min(pos_count, neg_count)
        
        # NEW: Check for rating mismatch (high rating but negative text)
        rating_match = re.search(r'(\d+)\s*stars?', text_lower)
        if rating_match:
            rating = int(rating_match.group(1))
            if rating >= 4 and neg_count > 0:
                sarcasm_score += 0.5
            elif rating <= 2 and pos_count > 0:
                sarcasm_score += 0.5
        
        return min(sarcasm_score, 0.95)
    
    def verify_batch_with_llm(self, reviews_batch):
        """
        Send multiple reviews in one LLM call for verification
        """
        # Prepare batch prompt - ultra concise
        prompt = """Analyze these reviews for sarcasm. Return JSON array with results.

Reviews:
"""
        for idx, review in enumerate(reviews_batch):
            # Truncate very long reviews
            review_text = review[:200] if len(review) > 200 else review
            prompt += f"{idx}: {review_text}\n"
        
        prompt += """

Respond with ONLY JSON array: [{"id":0,"sarcastic":true/false,"sentiment":"positive/negative/neutral"}, ...]
No other text. Max 10 tokens per review."""
        
        try:
            # Optimized LLM call with lower max_tokens
            response = ollama.chat(model='mistral', messages=[
                {'role': 'user', 'content': prompt}
            ], options={
                'num_predict': 100,  # Limit output tokens
                'temperature': 0.1,   # Lower temperature for consistency
                'top_k': 10,          # Reduce sampling
            })
            
            # Parse JSON response
            result_text = response['message']['content']
            json_match = re.search(r'\[.*\]', result_text, re.DOTALL)
            
            if json_match:
                results = json.loads(json_match.group())
                return results
            else:
                # Fallback: assume no sarcasm
                return [{"id": i, "sarcastic": False, "sentiment": "neutral"} 
                       for i in range(len(reviews_batch))]
                
        except Exception as e:
            print(f"⚠️ Batch LLM verification failed: {e}")
            return [{"id": i, "sarcastic": False, "sentiment": "neutral"} 
                   for i in range(len(reviews_batch))]
    
    def analyze_sentiment(self, text):
        """
        Fast sentiment analysis without LLM (for non-sarcastic reviews)
        """
        inputs = self.tokenizer(text, return_tensors="pt", truncation=True, max_length=512)
        
        with torch.no_grad():
            outputs = self.model(**inputs)
            probabilities = softmax(outputs.logits.numpy(), axis=1)
        
        sentiment_scores = {
            'Negative': probabilities[0][0],
            'Neutral': probabilities[0][1],
            'Positive': probabilities[0][2]
        }
        
        final_sentiment = max(sentiment_scores, key=sentiment_scores.get)
        
        return {
            'final_sentiment': final_sentiment,
            'sarcasm_detected': False,
            'sarcasm_probability': 0,
            'sentiment_scores': sentiment_scores
        }
    
    def analyze_batch_optimized(self, texts):
        """
        Optimized batch analysis with pre-filtering and LLM batching
        """
        self.stats['total_reviews'] = len(texts)
        results = []
        
        # Step 1: Fast detection for all reviews
        print("\n📊 Step 1: Fast sarcasm detection...")
        start_time = time.time()
        
        suspicious_indices = []
        fast_results = []
        
        for idx, text in enumerate(tqdm(texts, desc="Fast detection")):
            sarcasm_prob = self.detect_sarcasm_fast(str(text))
            fast_results.append(sarcasm_prob)
            
            if sarcasm_prob >= self.sarcasm_threshold:
                suspicious_indices.append(idx)
        
        self.stats['time_fast_detection'] = time.time() - start_time
        self.stats['fast_checks'] = len(texts)
        
        print(f"✅ Fast detection complete: {len(suspicious_indices)}/{len(texts)} reviews flagged for LLM verification")
        print(f"⏱️  Time: {self.stats['time_fast_detection']:.2f} seconds")
        
        # Step 2: Batch LLM verification for suspicious reviews
        self.stats['llm_calls'] = len(suspicious_indices)
        
        if suspicious_indices:
            print(f"\n🤖 Step 2: Batch LLM verification for {len(suspicious_indices)} suspicious reviews...")
            start_time = time.time()
            
            # Group suspicious reviews into batches
            batches = []
            for i in range(0, len(suspicious_indices), self.batch_llm_size):
                batch_indices = suspicious_indices[i:i + self.batch_llm_size]
                batch_texts = [str(texts[idx]) for idx in batch_indices]
                batches.append((batch_indices, batch_texts))
            
            self.stats['llm_batches'] = len(batches)
            
            # Process each batch
            llm_verifications = {}
            for batch_indices, batch_texts in tqdm(batches, desc="LLM batches"):
                batch_results = self.verify_batch_with_llm(batch_texts)
                
                # Map results back to indices
                for result in batch_results:
                    if isinstance(result, dict):
                        batch_idx = result.get('id', 0)
                        if batch_idx < len(batch_indices):
                            original_idx = batch_indices[batch_idx]
                            llm_verifications[original_idx] = result
            
            self.stats['time_llm_verification'] = time.time() - start_time
            print(f"✅ LLM verification complete: {self.stats['llm_batches']} batches")
            print(f"⏱️  Time: {self.stats['time_llm_verification']:.2f} seconds")
            
            # Step 3: Analyze each review with appropriate method
            for idx, text in enumerate(tqdm(texts, desc="Final analysis")):
                if idx in llm_verifications:
                    # Use LLM-verified result
                    llm_result = llm_verifications[idx]
                    is_sarcastic = llm_result.get('sarcastic', False)
                    
                    # Get base sentiment
                    base_analysis = self.analyze_sentiment(str(text))
                    
                    # Override with LLM sentiment if sarcastic
                    if is_sarcastic:
                        llm_sentiment = llm_result.get('sentiment', 'neutral').capitalize()
                        final_sentiment = llm_sentiment
                    else:
                        final_sentiment = base_analysis['final_sentiment']
                    
                    results.append({
                        'final_sentiment': final_sentiment,
                        'sarcasm_detected': is_sarcastic,
                        'sarcasm_probability': fast_results[idx],
                        'llm_verified': True,
                        'sentiment_scores': base_analysis['sentiment_scores'],
                        # In your results, add a confidence field
                        'confidence': 'high' if fast_results[idx] > 0.7 else 'medium' if fast_results[idx] > 0.3 else 'low'
                    })
                else:
                    # Use fast analysis only
                    analysis = self.analyze_sentiment(str(text))
                    results.append({
                        'final_sentiment': analysis['final_sentiment'],
                        'sarcasm_detected': False,
                        'sarcasm_probability': fast_results[idx],
                        'llm_verified': False,
                        'sentiment_scores': analysis['sentiment_scores'],
                        'confidence': 'high' if fast_results[idx] > 0.7 else 'medium' if fast_results[idx] > 0.3 else 'low'
                    })
        else:
            # No suspicious reviews, use fast analysis for all
            print("\n📊 No suspicious reviews found. Using fast analysis only...")
            for idx, text in enumerate(tqdm(texts, desc="Fast analysis")):
                analysis = self.analyze_sentiment(str(text))
                results.append({
                    'final_sentiment': analysis['final_sentiment'],
                    'sarcasm_detected': False,
                    'sarcasm_probability': fast_results[idx],
                    'llm_verified': False,
                    'sentiment_scores': analysis['sentiment_scores']
                })
        
        # Print performance statistics
        self.print_stats()
        
        return results
    
    def print_stats(self):
        """Print performance statistics"""
        print("\n" + "="*60)
        print("⚡ PERFORMANCE STATISTICS")
        print("="*60)
        print(f"📊 Total reviews analyzed: {self.stats['total_reviews']}")
        print(f"🔍 Fast sarcasm checks: {self.stats['fast_checks']}")
        print(f"🤖 LLM verified reviews: {self.stats['llm_calls']}")
        print(f"📦 LLM batches used: {self.stats['llm_batches']}")
        print(f"⏱️  Fast detection time: {self.stats['time_fast_detection']:.2f} sec")
        print(f"⏱️  LLM verification time: {self.stats['time_llm_verification']:.2f} sec")
        print(f"💨 Total time: {self.stats['time_fast_detection'] + self.stats['time_llm_verification']:.2f} sec")
        
        # Calculate speed improvement
        if self.stats['llm_calls'] > 0:
            avg_time_per_llm_review = self.stats['time_llm_verification'] / self.stats['llm_calls']
            print(f"⚡ Average time per LLM review: {avg_time_per_llm_review:.2f} sec")
            print(f"🚀 Estimated time without optimization: {self.stats['total_reviews'] * 34:.0f} sec")
            print(f"🎯 Speed improvement: {(self.stats['total_reviews'] * 34) / (self.stats['time_fast_detection'] + self.stats['time_llm_verification']):.1f}x")

def process_csv_optimized():
    """Process the CSV file with optimized analyzer"""
    print("\n📂 Loading reviews from CSV...")
    df = pd.read_csv('reviews.csv')
    
    # Combine title and content
    df['full_text'] = df['title'].fillna('') + " " + df['content'].fillna('')
    
    # Initialize optimized analyzer
    analyzer = OptimizedSentimentAnalyzer(sarcasm_threshold=0.3, batch_llm_size=5)
    
    # Analyze all reviews
    results = analyzer.analyze_batch_optimized(df['full_text'].tolist())
    
    # Add results to dataframe
    df['sentiment'] = [r['final_sentiment'] for r in results]
    df['sarcasm_detected'] = [r['sarcasm_detected'] for r in results]
    df['sarcasm_probability'] = [r['sarcasm_probability'] for r in results]
    df['llm_verified'] = [r['llm_verified'] for r in results]
    df['confidence'] = [r['confidence'] for r in results]
    df['sentiment_negative_score'] = [r['sentiment_scores']['Negative'] for r in results]
    df['sentiment_neutral_score'] = [r['sentiment_scores']['Neutral'] for r in results]
    df['sentiment_positive_score'] = [r['sentiment_scores']['Positive'] for r in results]
    
    # Save enriched dataset
    df.to_csv('analyzed_reviews_optimized.csv', index=False)
    
    # Print summary
    print("\n" + "="*60)
    print("📊 FINAL ANALYSIS SUMMARY")
    print("="*60)
    print(f"📊 Total Reviews: {len(df)}")
    print(f"\n🎭 Sentiment Distribution:")
    print(df['sentiment'].value_counts())
    print(f"\n😏 Sarcasm Statistics:")
    print(f"   - Reviews with sarcasm: {df['sarcasm_detected'].sum()}")
    print(f"   - Sarcasm percentage: {(df['sarcasm_detected'].sum()/len(df))*100:.1f}%")
    print(f"   - LLM verified: {df['llm_verified'].sum()}")
    
    # Show sarcastic reviews
    sarcastic_reviews = df[df['sarcasm_detected'] == True]
    if len(sarcastic_reviews) > 0:
        print("\n🔍 DETECTED SARCASTIC REVIEWS:")
        for idx, row in sarcastic_reviews.iterrows():
            print(f"\n   📝 {row['full_text'][:80]}...")
            print(f"   😏 Sarcasm Prob: {row['sarcasm_probability']:.2%}")
            print(f"   🎯 Sentiment: {row['sentiment']}")
            print(f"   🤖 LLM Verified: {'YES' if row['llm_verified'] else 'NO'}")
    
    print(f"\n✅ Results saved to 'analyzed_reviews_optimized.csv'")
    
    return df

if __name__ == "__main__":
    print("🚀 OPTIMIZED SENTIMENT ANALYZER WITH BATCHING")
    print("="*60)
    print("\n⚙️  Optimization features:")
    print("   • Pre-filtering: Only suspicious reviews go to LLM")
    print("   • Batch processing: 5 reviews per LLM call")
    print("   • Concise prompts: Reduced token usage")
    print("   • Lower temperature: Faster LLM responses")
    
    process_csv_optimized()