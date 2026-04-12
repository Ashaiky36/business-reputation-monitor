import streamlit as st
import pandas as pd
import os
import time
import threading
from datetime import datetime
import re
import sys

# Page config must be the first Streamlit command
st.set_page_config(
    page_title="Business Reputation Monitor",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Import your modules
from trustpilot_scraper import TrustpilotScraper
from enhanced_sentiment_analyzer import EnhancedSentimentAnalyzer
from extract_insights import extract_insights_improved
from pdf_report_generator import PDFReportGenerator
from email_reporter import EmailReporter

# Initialize session state
if 'app_stage' not in st.session_state:
    st.session_state.app_stage = 'setup'  # setup, processing, results
if 'scraped_data' not in st.session_state:
    st.session_state.scraped_data = None
if 'analysis_results' not in st.session_state:
    st.session_state.analysis_results = None
if 'business_info' not in st.session_state:
    st.session_state.business_info = {}

def validate_url(url):
    """Validate Trustpilot business URL"""
    pattern = r'https?://(www\.)?trustpilot\.com/review/[\w-]+'
    return re.match(pattern, url) is not None

def validate_email(email):
    """Validate email format"""
    pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    return re.match(pattern, email) is not None

def setup_screen():
    """Display the setup screen for business information"""
    
    st.markdown("""
    <style>
    .big-font {
        font-size: 20px !important;
        font-weight: bold;
    }
    .info-box {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        margin: 10px 0;
    }
    </style>
    """, unsafe_allow_html=True)
    
    st.title("🚀 Business Reputation Monitor")
    st.markdown("*AI-Powered Reputation Management System*")
    
    st.markdown("---")
    
    # Create two columns for layout
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("## 📝 Business Information")
        
        with st.form("business_setup"):
            # Business URL
            trustpilot_url = st.text_input(
                "Trustpilot Business URL *",
                placeholder="https://www.trustpilot.com/review/company-name",
                help="Enter the full Trustpilot review page URL for the business"
            )
            
            # Email for reports
            email = st.text_input(
                "Email Address *",
                placeholder="business@example.com",
                help="Reports will be sent to this email address"
            )
            
            # Optional business context
            business_name = st.text_input(
                "Business Name (Optional)",
                placeholder="e.g., Apple Inc.",
                help="Helps personalize the analysis"
            )
            
            business_context = st.text_area(
                "Business Context (Optional)",
                placeholder="Describe your business, products, services, or any specific concerns...",
                help="This helps our AI provide more accurate insights",
                height=100
            )
            
            # Report frequency
            report_frequency = st.selectbox(
                "Email Report Frequency",
                ["Daily", "Weekly", "Monthly"],
                help="How often you want to receive automated reports"
            )
            
            # Submit button
            submitted = st.form_submit_button("🚀 Start Analysis", type="primary", use_container_width=True)
            
            if submitted:
                # Validate inputs
                errors = []
                if not trustpilot_url:
                    errors.append("Trustpilot URL is required")
                elif not validate_url(trustpilot_url):
                    errors.append("Invalid Trustpilot URL format")
                
                if not email:
                    errors.append("Email address is required")
                elif not validate_email(email):
                    errors.append("Invalid email format")
                
                if errors:
                    for error in errors:
                        st.error(error)
                else:
                    # Store business info in session state
                    st.session_state.business_info = {
                        'trustpilot_url': trustpilot_url,
                        'email': email,
                        'business_name': business_name if business_name else "Business",
                        'business_context': business_context,
                        'report_frequency': report_frequency,
                        'start_time': datetime.now()
                    }
                    
                    st.session_state.app_stage = 'processing'
                    st.rerun()
    
    with col2:
        st.markdown("## 🎯 How It Works")
        st.markdown("""
        <div class="info-box">
        <b>1. 📊 Scrape Reviews</b><br>
        Collects 30 latest reviews from Trustpilot
        
        <br><br><b>2. 🤖 AI Analysis</b><br>
        Advanced sentiment & sarcasm detection
        
        <br><br><b>3. 💡 Generate Insights</b><br>
        Identifies problems and solutions
        
        <br><br><b>4. 📧 Email Reports</b><br>
        Automated reports to your inbox
        
        <br><br><b>5. 📈 Interactive Dashboard</b><br>
        Visual analytics in real-time
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        st.markdown("### 🔒 Privacy & Security")
        st.info("All data is processed locally. Your business information is never stored on external servers.")

def processing_screen():
    """Display processing screen with progress"""
    
    st.title("🔄 Processing Your Request")
    st.markdown(f"**Business:** {st.session_state.business_info.get('business_name', 'Processing...')}")
    st.markdown("---")
    
    # Create progress tracking
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    try:
        # Step 1: Scrape Trustpilot reviews
        status_text.markdown("**Step 1/4:** 📊 Scraping Trustpilot reviews...")
        progress_bar.progress(10)
        
        scraper = TrustpilotScraper()
        reviews_df = scraper.scrape_business_reviews(
            st.session_state.business_info['trustpilot_url'],
            num_reviews=30
        )
        
        if reviews_df is None or len(reviews_df) == 0:
            st.error("Failed to scrape reviews. Please check the URL and try again.")
            if st.button("◀ Back to Setup"):
                st.session_state.app_stage = 'setup'
                st.rerun()
            return
        
        st.session_state.scraped_data = reviews_df
        progress_bar.progress(30)
        status_text.markdown(f"✅ Scraped {len(reviews_df)} reviews successfully!")
        time.sleep(1)
        
        # Step 2: Sentiment Analysis
        status_text.markdown("**Step 2/4:** 🤖 Performing AI sentiment analysis...")
        progress_bar.progress(40)
        
        analyzer = EnhancedSentimentAnalyzer(
            use_llm_verification=True,
            sarcasm_threshold=0.3
        )
        
        # Prepare text for analysis
        reviews_df['full_text'] = reviews_df['title'].fillna('') + " " + reviews_df['content'].fillna('')
        results = analyzer.analyze_batch_optimized(reviews_df['full_text'].tolist())
        
        # Add results to dataframe
        reviews_df['sentiment'] = [r['final_sentiment'] for r in results]
        reviews_df['sarcasm_detected'] = [r['sarcasm_detected'] for r in results]
        reviews_df['sarcasm_probability'] = [r['sarcasm_probability'] for r in results]
        reviews_df['llm_verified'] = [r['llm_verified'] for r in results]
        reviews_df['confidence'] = [r.get('confidence', 'medium') for r in results]
        reviews_df['sentiment_negative_score'] = [r['sentiment_scores']['Negative'] for r in results]
        reviews_df['sentiment_neutral_score'] = [r['sentiment_scores']['Neutral'] for r in results]
        reviews_df['sentiment_positive_score'] = [r['sentiment_scores']['Positive'] for r in results]
        
        # Save analyzed data
        reviews_df.to_csv('analyzed_reviews_optimized.csv', index=False)
        st.session_state.analysis_results = reviews_df
        
        progress_bar.progress(70)
        status_text.markdown("✅ Sentiment analysis complete!")
        time.sleep(1)
        
        # Step 3: Generate Insights
        status_text.markdown("**Step 3/4:** 💡 Generating AI insights...")
        progress_bar.progress(80)
        
        insights = extract_insights_improved()
        if insights:
            with open('insights.json', 'w', encoding='utf-8') as f:
                json.dump(insights, f, indent=2)
            st.session_state.insights = insights
        
        progress_bar.progress(90)
        status_text.markdown("✅ Insights generated!")
        time.sleep(1)
        
        # Step 4: Setup Email Reporting
        status_text.markdown("**Step 4/4:** 📧 Configuring email reports...")
        progress_bar.progress(95)
        
        # Send initial report
        reporter = EmailReporter()
        reporter.send_report_email(
            st.session_state.business_info['email'],
            "initial",
            include_pdf=True
        )
        
        # Setup scheduled reports
        frequency = st.session_state.business_info['report_frequency']
        if frequency == "Daily":
            reporter.schedule_daily_report(st.session_state.business_info['email'], "09:00")
        elif frequency == "Weekly":
            reporter.schedule_weekly_report(st.session_state.business_info['email'], "monday", "09:00")
        
        # Start scheduler in background
        scheduler_thread = threading.Thread(target=reporter.run_scheduler, daemon=True)
        scheduler_thread.start()
        
        progress_bar.progress(100)
        status_text.markdown("✅ All complete! Redirecting to dashboard...")
        time.sleep(2)
        
        # Move to results screen
        st.session_state.app_stage = 'results'
        st.rerun()
        
    except Exception as e:
        st.error(f"An error occurred during processing: {str(e)}")
        st.error("Please check your inputs and try again.")
        
        if st.button("◀ Back to Setup"):
            st.session_state.app_stage = 'setup'
            st.rerun()

def results_screen():
    """Display the main dashboard with results"""
    
    # Import dashboard components
    from dashboard import (
        create_infographic, create_sentiment_chart, 
        create_sarcasm_indicator, display_insights
    )
    
    # Load data
    df = st.session_state.analysis_results
    with open('insights.json', 'r') as f:
        insights = json.load(f)
    
    # Header with business info
    st.title(f"📊 {st.session_state.business_info.get('business_name', 'Business')} Reputation Report")
    st.markdown(f"*Generated on: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}*")
    st.markdown(f"**Email Reports:** 📧 Sending to {st.session_state.business_info['email']} ({st.session_state.business_info['report_frequency']})")
    
    st.markdown("---")
    
    # Sidebar controls
    with st.sidebar:
        st.image("https://img.icons8.com/fluency/96/business-report.png", width=80)
        st.markdown("## 📊 Dashboard Controls")
        
        # Manual refresh option
        if st.button("🔄 Refresh Data", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
        
        st.markdown("---")
        st.markdown("### 📧 Report Settings")
        
        # Update email
        new_email = st.text_input("Update Email", value=st.session_state.business_info['email'])
        if new_email != st.session_state.business_info['email']:
            st.session_state.business_info['email'] = new_email
        
        # Send manual report
        if st.button("📧 Send Report Now", type="primary", use_container_width=True):
            reporter = EmailReporter()
            with st.spinner("Sending report..."):
                reporter.send_report_email(new_email, "ondemand", include_pdf=True)
                st.success(f"Report sent to {new_email}")
                st.info("Check MailHog at http://localhost:8025")
        
        st.markdown("---")
        st.markdown("### 📄 Export Options")
        
        # Generate PDF
        if st.button("📊 Generate PDF Report", use_container_width=True):
            generator = PDFReportGenerator(st.session_state.business_info.get('business_name', 'Business'))
            pdf_file = generator.generate_report("business_report.pdf")
            if os.path.exists(pdf_file):
                with open(pdf_file, "rb") as f:
                    st.download_button(
                        "Download PDF",
                        f.read(),
                        file_name=pdf_file,
                        mime="application/pdf"
                    )
        
        st.markdown("---")
        
        # Start new analysis
        if st.button("🆕 New Business Analysis", use_container_width=True):
            st.session_state.app_stage = 'setup'
            st.rerun()
        
        st.markdown("---")
        st.caption("Built with ❤️ using AI Technology")
    
    # Main dashboard tabs
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Dashboard", "🔍 Detailed Analysis", "📝 Review List", "📧 Email Reports"])
    
    with tab1:
        # Key metrics
        st.markdown("## 📈 Key Metrics")
        create_infographic(df)
        
        # Charts
        col1, col2 = st.columns(2)
        with col1:
            sentiment_chart = create_sentiment_chart(df)
            st.plotly_chart(sentiment_chart, use_container_width=True)
        with col2:
            sarcasm_gauge = create_sarcasm_indicator(df)
            st.plotly_chart(sarcasm_gauge, use_container_width=True)
        
        # Business context if provided
        if st.session_state.business_info.get('business_context'):
            with st.expander("📝 Business Context Provided"):
                st.info(st.session_state.business_info['business_context'])
        
        # AI Insights
        st.markdown("---")
        display_insights(insights)
    
    with tab2:
        st.markdown("## 🔍 Detailed Analysis")
        # Add detailed analysis from your original dashboard
        from dashboard import create_timeline_chart
        
        timeline = create_timeline_chart(df)
        if timeline:
            st.plotly_chart(timeline, use_container_width=True)
        
        # Sentiment distribution by confidence
        confidence_counts = df['confidence'].value_counts()
        fig = px.bar(x=confidence_counts.index, y=confidence_counts.values,
                    title="Analysis Confidence Levels",
                    color=confidence_counts.index,
                    color_discrete_map={'high': 'green', 'medium': 'orange', 'low': 'red'})
        st.plotly_chart(fig, use_container_width=True)
    
    with tab3:
        st.markdown("## 📝 All Reviews")
        
        # Search and filter
        search_term = st.text_input("🔍 Search reviews", placeholder="Enter keyword...")
        sentiment_filter = st.multiselect("Filter by Sentiment", 
                                         options=['Positive', 'Neutral', 'Negative'],
                                         default=['Positive', 'Neutral', 'Negative'])
        
        filtered_df = df[df['sentiment'].isin(sentiment_filter)]
        if search_term:
            filtered_df = filtered_df[filtered_df['full_text'].str.contains(search_term, case=False, na=False)]
        
        for idx, row in filtered_df.head(50).iterrows():
            sentiment_color = {'Positive': '🟢', 'Neutral': '⚪', 'Negative': '🔴'}.get(row['sentiment'], '⚪')
            sarcasm_badge = " 😏" if row['sarcasm_detected'] else ""
            
            st.markdown(f"""
            <div style="background: white; padding: 1rem; border-radius: 10px; margin-bottom: 1rem; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                <div style="display: flex; justify-content: space-between;">
                    <div>
                        <span style="font-size: 1.5rem;">{sentiment_color}</span>
                        <strong>{row['sentiment']}</strong>{sarcasm_badge}
                        <span style="color: #888; margin-left: 1rem;">Confidence: {row.get('confidence', 'medium').upper()}</span>
                    </div>
                    <small style="color: #888;">{row.get('date', 'No date')}</small>
                </div>
                <p style="margin-top: 0.5rem;">{row['full_text']}</p>
            </div>
            """, unsafe_allow_html=True)
    
    with tab4:
        st.markdown("## 📧 Email Report Configuration")
        
        st.markdown("### Current Settings")
        st.info(f"""
        - **Recipient Email:** {st.session_state.business_info['email']}
        - **Report Frequency:** {st.session_state.business_info['report_frequency']}
        - **Next Scheduled Report:** {get_next_report_time(st.session_state.business_info['report_frequency'])}
        """)
        
        st.markdown("### Report History")
        st.markdown("*Reports are sent automatically based on your schedule.*")
        
        st.markdown("### Manual Report")
        if st.button("📧 Send Test Report Now", type="primary"):
            reporter = EmailReporter()
            reporter.send_report_email(st.session_state.business_info['email'], "test", include_pdf=True)
            st.success(f"Test report sent to {st.session_state.business_info['email']}")

def get_next_report_time(frequency):
    """Calculate next report time"""
    from datetime import datetime, timedelta
    
    now = datetime.now()
    if frequency == "Daily":
        next_time = now.replace(hour=9, minute=0, second=0, microsecond=0)
        if now >= next_time:
            next_time += timedelta(days=1)
        return next_time.strftime("%B %d, %Y at 9:00 AM")
    elif frequency == "Weekly":
        days_ahead = 0 - now.weekday()  # Monday = 0
        if days_ahead <= 0:
            days_ahead += 7
        next_monday = now + timedelta(days=days_ahead)
        next_monday = next_monday.replace(hour=9, minute=0, second=0, microsecond=0)
        return next_monday.strftime("%B %d, %Y at 9:00 AM")
    else:
        return "Schedule configured"

# Main app routing
def main():
    if st.session_state.app_stage == 'setup':
        setup_screen()
    elif st.session_state.app_stage == 'processing':
        processing_screen()
    elif st.session_state.app_stage == 'results':
        results_screen()

if __name__ == "__main__":
    import json
    main()