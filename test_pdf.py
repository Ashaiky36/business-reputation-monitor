from pdf_report_generator import PDFReportGenerator
import pandas as pd
import json

# Create sample data if needed
def create_sample_data():
    """Create sample data for testing"""
    # Check if files exist
    try:
        df = pd.read_csv('analyzed_reviews_optimized.csv')
        with open('insights.json', 'r') as f:
            insights = json.load(f)
        return True
    except:
        print("Please run sentiment analyzer first")
        return False

if __name__ == "__main__":
    print("Testing PDF Report Generation...")
    
    if create_sample_data():
        generator = PDFReportGenerator("Test Business Report")
        generator.generate_report("test_report.pdf")
        print("\n✅ Test report generated: test_report.pdf")
    else:
        print("❌ Please run sentiment_analyzer.py first")