import pandas as pd
import ollama
import json
import re
from tqdm import tqdm
import time

#takes too much time since it feeds every review into the llm. only 1-2 to reviews were
#processed in 15 minutes last time I ran this script.

def load_reviews(csv_file='reviews.csv'):
    """Load reviews from CSV file"""
    df = pd.read_csv(csv_file)
    print(f"✅ Loaded {len(df)} reviews from {csv_file}")
    return df

def analyze_with_llm(text, review_index):
    """Send single review to LLM for sentiment analysis"""
    
    prompt = f"""You are a sentiment analysis expert. Analyze the following customer review and provide sentiment analysis.

Review: "{text}"

Respond with ONLY a valid JSON object in this exact format:
{{
    "sentiment": "positive/negative/neutral",
    "is_sarcastic": true/false,
    "confidence": 0.0-1.0,
    "key_issues": "brief description of main complaints if negative, otherwise empty string",
    "explanation": "brief reason for your classification"
}}

Do not include any other text outside the JSON object."""
    
    try:
        response = ollama.chat(model='mistral', messages=[
            {'role': 'user', 'content': prompt}
        ], options={'temperature': 0.1})  # Low temperature for consistent results
        
        result_text = response['message']['content']
        
        # Extract JSON from response
        json_match = re.search(r'\{.*\}', result_text, re.DOTALL)
        if json_match:
            result = json.loads(json_match.group())
        else:
            # Fallback if JSON parsing fails
            result = {
                "sentiment": "neutral",
                "is_sarcastic": False,
                "confidence": 0.5,
                "key_issues": "",
                "explanation": "Failed to parse LLM response"
            }
        
        return result
        
    except Exception as e:
        print(f"\n❌ Error analyzing review {review_index}: {e}")
        return {
            "sentiment": "neutral",
            "is_sarcastic": False,
            "confidence": 0.0,
            "key_issues": "",
            "explanation": f"Error: {str(e)}"
        }

def main():
    print("="*60)
    print("🔍 LLM SENTIMENT VERIFICATION FOR ALL REVIEWS")
    print("="*60)
    
    # Load reviews
    df = load_reviews('reviews.csv')
    
    # Combine title and content for better context
    df['full_text'] = df['title'].fillna('') + " " + df['content'].fillna('')
    
    # Store results
    results = []
    
    print(f"\n📝 Analyzing {len(df)} reviews with Mistral...")
    print("⏱️  This may take a minute or two...\n")
    
    # Analyze each review
    for idx, row in tqdm(df.iterrows(), total=len(df), desc="Processing reviews"):
        text = row['full_text'].strip()
        if not text:
            text = row['content'] if pd.notna(row['content']) else "No content"
        
        # Add review number for context
        print(f"\n📋 Review #{idx+1}:")
        print(f"   Text: {text[:100]}..." if len(text) > 100 else f"   Text: {text}")
        
        # Get LLM analysis
        result = analyze_with_llm(text, idx)
        results.append(result)
        
        # Display result
        sentiment_emoji = {
            'positive': '✅',
            'negative': '❌',
            'neutral': '⚪'
        }.get(result['sentiment'], '❓')
        
        sarcasm_mark = '😏 SARCASTIC' if result['is_sarcastic'] else '📝 Literal'
        
        print(f"   {sentiment_emoji} Sentiment: {result['sentiment'].upper()}")
        print(f"   {sarcasm_mark}")
        print(f"   📊 Confidence: {result['confidence']:.2%}")
        if result.get('key_issues'):
            print(f"   ⚠️ Issues: {result['key_issues'][:100]}")
        print(f"   💡 {result['explanation'][:100]}")
        print("-"*40)
        
        # Small delay to avoid overwhelming Ollama
        time.sleep(0.5)
    
    # Add results to dataframe
    df['llm_sentiment'] = [r['sentiment'] for r in results]
    df['llm_is_sarcastic'] = [r['is_sarcastic'] for r in results]
    df['llm_confidence'] = [r['confidence'] for r in results]
    df['llm_key_issues'] = [r.get('key_issues', '') for r in results]
    df['llm_explanation'] = [r.get('explanation', '') for r in results]
    
    # Save results
    output_file = 'llm_verified_reviews.csv'
    df.to_csv(output_file, index=False)
    
    # Print summary
    print("\n" + "="*60)
    print("📊 SUMMARY STATISTICS")
    print("="*60)
    
    sentiment_counts = df['llm_sentiment'].value_counts()
    for sentiment, count in sentiment_counts.items():
        percentage = (count / len(df)) * 100
        print(f"{sentiment.upper()}: {count} reviews ({percentage:.1f}%)")
    
    sarcastic_count = df['llm_is_sarcastic'].sum()
    print(f"\n😏 Sarcastic reviews detected: {sarcastic_count}/{len(df)} ({sarcastic_count/len(df)*100:.1f}%)")
    
    avg_confidence = df['llm_confidence'].mean()
    print(f"📊 Average confidence score: {avg_confidence:.2%}")
    
    # Show problematic reviews (low confidence)
    low_confidence = df[df['llm_confidence'] < 0.7]
    if len(low_confidence) > 0:
        print(f"\n⚠️ Reviews with low confidence (<70%):")
        for idx, row in low_confidence.iterrows():
            print(f"   Review #{idx+1}: {row['full_text'][:80]}...")
            print(f"   Confidence: {row['llm_confidence']:.2%}")
    
    # Display sarcastic reviews
    sarcastic_reviews = df[df['llm_is_sarcastic'] == True]
    if len(sarcastic_reviews) > 0:
        print("\n" + "="*60)
        print("🔍 SARCASTIC REVIEWS DETECTED")
        print("="*60)
        for idx, row in sarcastic_reviews.iterrows():
            print(f"\n📝 Review #{idx+1}: {row['full_text'][:150]}")
            print(f"   Sentiment: {row['llm_sentiment'].upper()}")
            print(f"   Explanation: {row['llm_explanation'][:100]}")
    
    print(f"\n✅ Results saved to '{output_file}'")
    print("\n📁 You can now compare with your previous analysis:")
    print("   - Original: reviews.csv")
    print("   - Enhanced: analyzed_reviews_enhanced.csv")
    print("   - LLM Verified: llm_verified_reviews.csv")

def compare_with_previous():
    """Optional: Compare LLM results with previous analyzer"""
    try:
        enhanced = pd.read_csv('analyzed_reviews_enhanced.csv')
        llm = pd.read_csv('llm_verified_reviews.csv')
        
        print("\n" + "="*60)
        print("📊 COMPARISON: Enhanced Analyzer vs Pure LLM")
        print("="*60)
        
        # Map sentiments to comparable format
        enhanced_sentiment = enhanced['sentiment'].value_counts()
        llm_sentiment = llm['llm_sentiment'].value_counts()
        
        print("\nEnhanced Analyzer Results:")
        for sentiment, count in enhanced_sentiment.items():
            print(f"  {sentiment}: {count}")
        
        print("\nPure LLM Results:")
        for sentiment, count in llm_sentiment.items():
            print(f"  {sentiment}: {count}")
        
        # Check agreement
        if len(enhanced) == len(llm):
            agreement = (enhanced['sentiment'].str.lower() == llm['llm_sentiment']).mean()
            print(f"\n🤝 Agreement between methods: {agreement:.1%}")
            
            # Show disagreements
            disagreements = enhanced[enhanced['sentiment'].str.lower() != llm['llm_sentiment']]
            if len(disagreements) > 0:
                print(f"\n⚠️ Disagreements found in {len(disagreements)} reviews:")
                for idx, row in disagreements.iterrows():
                    print(f"\n  Review: {row['full_text'][:100]}...")
                    print(f"  Enhanced: {row['sentiment']} | LLM: {row['llm_sentiment']}")
                    
    except FileNotFoundError:
        print("\nℹ️  Run enhanced_sentiment_analyzer.py first to enable comparison")

if __name__ == "__main__":
    main()
    
    # Ask if user wants comparison
    response = input("\n📊 Compare with previous enhanced analyzer results? (yes/no): ").lower()
    if response in ['yes', 'y']:
        compare_with_previous()