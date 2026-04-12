import pandas as pd
import ollama
import json
import re
import random
from datetime import datetime
import sys

# Fix for Windows console encoding issues
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

def safe_json_parse(response_text):
    """
    Safely parse JSON from LLM response that might include extra text
    """
    # Try direct parsing first
    try:
        return json.loads(response_text)
    except:
        pass
    
    # Try to extract JSON between curly braces
    try:
        # Find content between first { and last }
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
    except:
        pass
    
    # Try to extract using markdown code blocks
    try:
        code_block_match = re.search(r'```json\s*(.*?)\s*```', response_text, re.DOTALL)
        if code_block_match:
            return json.loads(code_block_match.group(1))
    except:
        pass
    
    # If all fails, create a structured fallback response
    print("⚠️ Warning: Could not parse JSON from LLM response. Using fallback.")
    print(f"Raw response: {response_text[:200]}...")
    
    return {
        "problems": ["Unable to parse LLM response"],
        "suggestions": ["Please check the LLM output format"],
        "raw_response": response_text[:500]
    }

def extract_insights_improved():
    """
    Extract insights from negative reviews with random sampling and robust parsing
    """
    print("🚀 STARTING ENHANCED INSIGHTS EXTRACTION")
    print("="*60)
    
    # Load analyzed reviews
    print("\n📂 Loading analyzed reviews...")
    df = pd.read_csv('analyzed_reviews_optimized.csv')
    
    # Extract negative reviews
    negative_reviews = df[df['sentiment'] == 'Negative']
    
    print(f"📊 Total reviews analyzed: {len(df)}")
    print(f"🔴 Negative reviews found: {len(negative_reviews)}")
    print(f"🟢 Positive reviews: {len(df[df['sentiment'] == 'Positive'])}")
    print(f"⚪ Neutral reviews: {len(df[df['sentiment'] == 'Neutral'])}")
    
    if len(negative_reviews) == 0:
        print("\n⚠️ No negative reviews found to analyze!")
        return None
    
    # Sample random negative reviews (or take all if less than sample size)
    sample_size = min(10, len(negative_reviews))
    
    if len(negative_reviews) > sample_size:
        sampled_reviews = negative_reviews.sample(n=sample_size, random_state=42)
        print(f"\n🎲 Randomly selected {sample_size} negative reviews out of {len(negative_reviews)} for insights")
    else:
        sampled_reviews = negative_reviews
        print(f"\n📝 Using all {len(negative_reviews)} negative reviews for insights")
    
    # Save negative reviews for reference (handle encoding)
    try:
        sampled_reviews[['full_text', 'sentiment', 'sarcasm_detected', 'confidence']].to_csv('sampled_negative_reviews.csv', index=False, encoding='utf-8-sig')
        print(f"💾 Saved sampled negative reviews to 'sampled_negative_reviews.csv'")
    except Exception as e:
        print(f"⚠️ Could not save CSV: {e}")
    
    # Prepare reviews for LLM (with truncation to save tokens)
    review_texts = []
    for idx, row in sampled_reviews.iterrows():
        # Truncate very long reviews to save processing time
        review = row['full_text'][:300] if len(row['full_text']) > 300 else row['full_text']
        sarcasm_note = " [SARCASM DETECTED]" if row.get('sarcasm_detected', False) else ""
        confidence_note = f" (Confidence: {row.get('confidence', 'medium')})" if row.get('confidence') else ""
        review_texts.append(f"- {review}{sarcasm_note}{confidence_note}")
    
    reviews_block = "\n\n".join(review_texts)
    
    # Enhanced prompt with explicit formatting instructions
    prompt = f"""You are analyzing customer reviews for a business reputation tool. 

Based on these {len(review_texts)} negative customer reviews, identify the main problems and provide actionable solutions.

REVIEWS:
{reviews_block}

INSTRUCTIONS:
1. Identify the top 3-5 most common problems mentioned
2. For each problem, provide a specific, actionable suggestion
3. Respond ONLY with valid JSON in this exact format:
{{
    "problems": ["Problem 1 description", "Problem 2 description", "Problem 3 description"],
    "suggestions": ["Suggestion for problem 1", "Suggestion for problem 2", "Suggestion for problem 3"],
    "severity": ["High", "Medium", "Low"]
}}

Do not include any other text, explanations, or markdown formatting outside the JSON."""
    
    print("\n🤖 Generating insights using Ollama Mistral...")
    print(f"⏱️  This may take 30-60 seconds for {len(review_texts)} reviews...")
    
    try:
        # Make LLM call with timeout handling
        response = ollama.chat(
            model='mistral',
            messages=[
                {
                    'role': 'system', 
                    'content': 'You are a precise JSON generator. Always respond with valid JSON only, no additional text.'
                },
                {
                    'role': 'user', 
                    'content': prompt
                }
            ],
            options={
                'temperature': 0.3,
                'num_predict': 500,
            }
        )
        
        # Parse JSON safely
        insights = safe_json_parse(response['message']['content'])
        
        # Validate required fields
        if 'problems' not in insights or 'suggestions' not in insights:
            print("⚠️ Missing required fields in LLM response. Using fallback structure.")
            insights = {
                "problems": insights.get('problems', ['Issue with product/service']),
                "suggestions": insights.get('suggestions', ['Review customer feedback for patterns']),
                "severity": insights.get('severity', ['Medium'])
            }
        
        # Ensure we have matching lengths
        if len(insights['problems']) != len(insights['suggestions']):
            print(f"⚠️ Mismatched lengths: {len(insights['problems'])} problems vs {len(insights['suggestions'])} suggestions")
            min_len = min(len(insights['problems']), len(insights['suggestions']))
            insights['problems'] = insights['problems'][:min_len]
            insights['suggestions'] = insights['suggestions'][:min_len]
            if 'severity' in insights:
                insights['severity'] = insights['severity'][:min_len]
        
        # Save insights to JSON with proper encoding
        with open('insights.json', 'w', encoding='utf-8') as f:
            json.dump(insights, f, indent=2, ensure_ascii=False)
        
        print("\n" + "="*60)
        print("✅ INSIGHTS GENERATED SUCCESSFULLY")
        print("="*60)
        print("\n📊 KEY PROBLEMS IDENTIFIED:")
        for i, problem in enumerate(insights['problems'], 1):
            severity = insights.get('severity', [''] * len(insights['problems']))
            severity_text = f" [{severity[i-1]} Severity]" if i-1 < len(severity) and severity[i-1] else ""
            print(f"\n{i}. {problem}{severity_text}")
            if i-1 < len(insights['suggestions']):
                print(f"   --> Suggestion: {insights['suggestions'][i-1]}")
        
        print(f"\n💾 Insights saved to 'insights.json'")
        
        # Generate human-readable report with proper encoding
        generate_readable_report(insights, negative_reviews)
        
        return insights
        
    except Exception as e:
        print(f"\n❌ Error generating insights: {e}")
        print("Creating fallback insights...")
        
        fallback_insights = {
            "problems": [
                "Unable to analyze reviews due to technical issue",
                "Please check Ollama connection",
                "Review data may need verification"
            ],
            "suggestions": [
                "Run the sentiment analyzer again",
                "Verify Ollama is running: 'ollama list'",
                "Check CSV file format and content"
            ],
            "severity": ["High", "Medium", "Low"]
        }
        
        with open('insights_fallback.json', 'w', encoding='utf-8') as f:
            json.dump(fallback_insights, f, indent=2, ensure_ascii=False)
        
        print("💾 Fallback insights saved to 'insights_fallback.json'")
        return fallback_insights

def generate_readable_report(insights, negative_reviews):
    """
    Generate a human-readable text report from insights (without Unicode arrows)
    """
    try:
        # Calculate sarcastic count safely
        sarcastic_count = 0
        if 'sarcasm_detected' in negative_reviews.columns:
            sarcastic_count = len(negative_reviews[negative_reviews['sarcasm_detected'] == True])
        
        report = f"""
BUSINESS REPUTATION INSIGHTS REPORT
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
{'='*60}

SUMMARY STATISTICS
-----------------
Total Negative Reviews Analyzed: {len(negative_reviews)}
Sarcastic Negative Reviews: {sarcastic_count}

KEY PROBLEMS IDENTIFIED
----------------------
"""
        for i, problem in enumerate(insights['problems'], 1):
            report += f"\n{i}. {problem}"
            if i-1 < len(insights.get('suggestions', [])):
                report += f"\n   SUGGESTED ACTION: {insights['suggestions'][i-1]}\n"
        
        if 'severity' in insights and insights['severity']:
            report += f"\nSEVERITY LEVELS\n"
            report += "-" * 30 + "\n"
            for i, severity in enumerate(insights['severity']):
                if i < len(insights['problems']):
                    report += f"Problem {i+1}: {severity} Severity\n"
        
        report += f"""
{'='*60}
ACTION ITEMS
-----------
1. Prioritize issues based on severity levels
2. Implement suggested solutions within 2 weeks
3. Monitor future reviews for improvement
4. Respond to negative reviews professionally

END OF REPORT
"""
        
        # Write with UTF-8 encoding for Windows compatibility
        with open('insights_report.txt', 'w', encoding='utf-8') as f:
            f.write(report)
        
        print("📄 Human-readable report saved to 'insights_report.txt'")
        
    except Exception as e:
        print(f"⚠️ Could not generate readable report: {e}")
        # Create a simpler fallback report
        try:
            simple_report = f"Report generated on {datetime.now()}\nProblems: {', '.join(insights['problems'])}"
            with open('insights_report.txt', 'w', encoding='utf-8') as f:
                f.write(simple_report)
            print("📄 Simple report saved to 'insights_report.txt'")
        except:
            print("❌ Could not save report file")

def quick_test():
    """
    Quick test function to verify JSON parsing
    """
    test_responses = [
        '{"problems": ["Test problem"], "suggestions": ["Test suggestion"]}',
        'Sure! Here is your JSON: {"problems": ["Test"], "suggestions": ["Test"]}',
        '```json\n{"problems": ["Test"], "suggestions": ["Test"]}\n```',
        'Invalid response here'
    ]
    
    print("Testing JSON parsing robustness...")
    for i, response in enumerate(test_responses, 1):
        result = safe_json_parse(response)
        print(f"Test {i}: {'✅' if 'problems' in result else '❌'}")

if __name__ == "__main__":
    # Run quick test first
    quick_test()
    
    print("\n" + "="*60)
    response = input("\n🚀 Run full insights extraction? (yes/no): ").lower()
    
    if response in ['yes', 'y']:
        insights = extract_insights_improved()
        
        if insights:
            print("\n🎉 Insights extraction complete! Ready for dashboard integration.")
            print("\n📁 Generated files:")
            print("   - insights.json (structured data for dashboard)")
            print("   - insights_report.txt (human-readable report)")
            print("   - sampled_negative_reviews.csv (sample data used)")
        else:
            print("\n⚠️ Insights extraction encountered issues. Check the error messages above.")
    else:
        print("\n✅ Test completed. Run the script again when ready to extract insights.")