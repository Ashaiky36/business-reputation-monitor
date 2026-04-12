import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json
from datetime import datetime
import base64
from io import BytesIO
import ollama
import os
import threading
import socket
from email_reporter import EmailReporter

# Page configuration
st.set_page_config(
    page_title="Business Reputation Monitor",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for modern styling
st.markdown("""
<style>
    /* Modern gradient background */
    .stApp {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }
    
    /* Card styling */
    .css-1r6slb0 {
        background: rgba(255, 255, 255, 0.95);
        border-radius: 20px;
        padding: 1.5rem;
        box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.37);
        backdrop-filter: blur(4px);
        border: 1px solid rgba(255, 255, 255, 0.18);
    }
    
    /* Metric cards */
    .metric-card {
        background: white;
        border-radius: 15px;
        padding: 1rem;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        transition: transform 0.3s;
    }
    
    .metric-card:hover {
        transform: translateY(-5px);
    }
    
    /* Headers */
    h1 {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 3rem !important;
    }
    
    /* Sidebar styling */
    .css-1d391kg {
        background: rgba(255,255,255,0.95);
        backdrop-filter: blur(10px);
    }
</style>
""", unsafe_allow_html=True)

# Initialize email reporter
def init_email_reporter():
    """Initialize email reporter from environment variables or defaults"""
    sender_email = os.getenv('SENDER_EMAIL', 'test@business-reputation.local')
    sender_password = os.getenv('SENDER_PASSWORD', 'any_password')
    smtp_server = os.getenv('SMTP_SERVER', 'localhost')
    smtp_port = int(os.getenv('SMTP_PORT', '1025'))
    
    return EmailReporter(sender_email, sender_password, smtp_server, smtp_port)

def send_immediate_report(email, reporter):
    """Send immediate report to email"""
    if reporter:
        with st.spinner("📤 Generating and sending report..."):
            success = reporter.send_report_email(email, "ondemand", include_pdf=True)
            if success:
                st.success(f"✅ Report sent successfully to {email}")
                st.balloons()
                st.info("💡 Check MailHog at http://localhost:8025 to view the email")
            else:
                st.error("❌ Failed to send report. Is MailHog running?")
                st.info("Make sure MailHog is running in a terminal window")
    else:
        st.error("❌ Email not configured. Please setup email first.")

def schedule_reports(email, frequency, reporter):
    """Schedule recurring reports"""
    if reporter:
        if frequency == "Daily":
            reporter.schedule_daily_report(email, "09:00")
            st.success(f"✅ Daily reports scheduled for {email} at 9:00 AM")
        elif frequency == "Weekly":
            reporter.schedule_weekly_report(email, "monday", "09:00")
            st.success(f"✅ Weekly reports scheduled for {email} on Mondays at 9:00 AM")
        elif frequency == "Monthly":
            st.info("Monthly scheduling coming soon!")
        
        # Start scheduler in background thread
        if 'scheduler_running' not in st.session_state:
            scheduler_thread = threading.Thread(target=reporter.run_scheduler, daemon=True)
            scheduler_thread.start()
            st.session_state.scheduler_running = True
            st.info("📅 Scheduler started in background")
    else:
        st.error("❌ Email not configured")

def generate_and_download_pdf():
    """Generate PDF and provide download button"""
    from pdf_report_generator import PDFReportGenerator
    
    try:
        generator = PDFReportGenerator(company_name="Business Reputation Report")
        pdf_file = "business_insights_report.pdf"
        
        with st.spinner("Generating PDF report..."):
            success = generator.generate_report(pdf_file)
        
        if success and os.path.exists(pdf_file):
            with open(pdf_file, "rb") as f:
                pdf_bytes = f.read()
            
            st.download_button(
                label="📥 Download PDF Report",
                data=pdf_bytes,
                file_name=pdf_file,
                mime="application/pdf",
                use_container_width=True
            )
            return True
        else:
            st.error("Failed to generate PDF report")
            return False
    except Exception as e:
        st.error(f"Error generating PDF: {e}")
        return False

# Load data
@st.cache_data
def load_data():
    """Load and cache all data"""
    try:
        df = pd.read_csv('analyzed_reviews_optimized.csv')
        
        # Load insights
        with open('insights.json', 'r', encoding='utf-8') as f:
            insights = json.load(f)
        
        return df, insights
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return None, None

def create_sentiment_chart(df):
    """Create interactive sentiment distribution chart"""
    sentiment_counts = df['sentiment'].value_counts()
    
    colors = {
        'Positive': '#00ff88',
        'Neutral': '#ffb347',
        'Negative': '#ff4757'
    }
    
    fig = go.Figure(data=[
        go.Pie(
            labels=sentiment_counts.index,
            values=sentiment_counts.values,
            hole=0.4,
            marker_colors=[colors.get(s, '#888') for s in sentiment_counts.index],
            textinfo='label+percent',
            textposition='auto',
            hovertemplate='<b>%{label}</b><br>Count: %{value}<br>Percentage: %{percent}<extra></extra>'
        )
    ])
    
    fig.update_layout(
        title="Sentiment Distribution",
        title_font_size=20,
        showlegend=True,
        height=400,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)'
    )
    
    return fig

def create_sarcasm_indicator(df):
    """Create sarcasm detection gauge"""
    sarcasm_count = df['sarcasm_detected'].sum()
    sarcasm_percentage = (sarcasm_count / len(df)) * 100
    
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=sarcasm_percentage,
        title={'text': "Sarcasm Detection Rate", 'font': {'size': 24}},
        delta={'reference': 10, 'increasing': {'color': "red"}},
        gauge={
            'axis': {'range': [None, 100], 'tickwidth': 1},
            'bar': {'color': "darkorange"},
            'steps': [
                {'range': [0, 20], 'color': "lightgreen"},
                {'range': [20, 50], 'color': "orange"},
                {'range': [50, 100], 'color': "red"}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': 30
            }
        }
    ))
    
    fig.update_layout(height=300, paper_bgcolor='rgba(0,0,0,0)')
    return fig

def create_timeline_chart(df):
    """Create review timeline if date column exists"""
    if 'date' in df.columns:
        df['date'] = pd.to_datetime(df['date'])
        timeline = df.groupby([df['date'].dt.date, 'sentiment']).size().reset_index(name='count')
        
        fig = px.line(timeline, x='date', y='count', color='sentiment',
                      title="Review Trends Over Time",
                      labels={'count': 'Number of Reviews', 'date': 'Date'})
        fig.update_layout(height=400, paper_bgcolor='rgba(0,0,0,0)')
        return fig
    return None

def display_insights(insights):
    """Display AI-generated insights in beautiful cards"""
    st.markdown("## 💡 AI-Powered Insights")
    
    cols = st.columns(len(insights['problems']))
    
    severity_colors = {
        'High': '#ff4757',
        'Medium': '#ffb347',
        'Low': '#00ff88'
    }
    
    for idx, (col, problem, suggestion, severity) in enumerate(zip(cols, insights['problems'], insights['suggestions'], insights.get('severity', ['Medium']*len(insights['problems'])))):
        with col:
            color = severity_colors.get(severity, '#888')
            st.markdown(f"""
            <div class="metric-card" style="padding: 1rem; border-top: 4px solid {color};">
                <h3 style="color: {color}; margin: 0;">⚠️ Problem {idx+1}</h3>
                <p style="font-size: 1.1rem; font-weight: bold;">{problem}</p>
                <p style="color: {color}; font-size: 0.9rem;">Severity: {severity}</p>
                <hr>
                <p><strong>💡 Solution:</strong><br>{suggestion}</p>
            </div>
            """, unsafe_allow_html=True)

def create_infographic(df):
    """Create infographic-style metrics"""
    total_reviews = len(df)
    negative_count = len(df[df['sentiment'] == 'Negative'])
    positive_count = len(df[df['sentiment'] == 'Positive'])
    neutral_count = len(df[df['sentiment'] == 'Neutral'])
    sarcasm_count = df['sarcasm_detected'].sum()
    
    # Create metrics row
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric("📊 Total Reviews", total_reviews, delta=None)
    with col2:
        st.metric("🔴 Negative", negative_count, delta=f"{(negative_count/total_reviews)*100:.1f}%")
    with col3:
        st.metric("🟢 Positive", positive_count, delta=f"{(positive_count/total_reviews)*100:.1f}%")
    with col4:
        st.metric("⚪ Neutral", neutral_count, delta=f"{(neutral_count/total_reviews)*100:.1f}%")
    with col5:
        st.metric("😏 Sarcastic Reviews", sarcasm_count, delta=f"{(sarcasm_count/total_reviews)*100:.1f}%")

def main():
    # Header
    st.title("📈 Business Reputation Monitoring System")
    st.markdown("*AI-Powered Sentiment Analysis & Reputation Management*")
    
    # Load data
    df, insights = load_data()
    
    if df is None or insights is None:
        st.error("Failed to load data. Please ensure 'analyzed_reviews_optimized.csv' and 'insights.json' exist.")
        return
    
    # Sidebar - Email Reports
    with st.sidebar:
        st.image("https://img.icons8.com/fluency/96/business-report.png", width=80)
        st.markdown("## 📧 Email Reports")
        
        # Initialize reporter
        reporter = init_email_reporter()
        
        # Check MailHog status
        st.markdown("### 📬 Email Server Status")
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex(('localhost', 8025))
            sock.close()
            
            if result == 0:
                st.success("✅ MailHog is running")
                st.caption("View emails at: http://localhost:8025")
            else:
                st.warning("⚠️ MailHog not detected")
                st.caption("Run MailHog.exe to enable email preview")
        except:
            st.warning("⚠️ Cannot check MailHog status")
        
        st.markdown("---")
        
        # Email input
        email = st.text_input("Recipient Email", placeholder="business@example.com", key="recipient_email")
        
        col1, col2 = st.columns(2)
        with col1:
            report_type = st.selectbox("Report Type", ["Daily", "Weekly", "Monthly"])
        with col2:
            include_pdf = st.checkbox("Attach PDF", value=True)
        
        # Send now button
        if st.button("📧 Send Report Now", type="primary", use_container_width=True):
            if email:
                send_immediate_report(email, reporter)
            else:
                st.warning("Please enter recipient email")
        
        # Schedule button
        if st.button("⏰ Schedule Reports", use_container_width=True):
            if email:
                schedule_reports(email, report_type, reporter)
            else:
                st.warning("Please enter recipient email")
        
        st.markdown("---")
        st.markdown("### 📄 Report Generation")
        
        if st.button("📊 Generate PDF Report", type="primary", use_container_width=True):
            generate_and_download_pdf()
        
        st.markdown("---")
        st.info("💡 **Tip:** Reports include sentiment analysis, AI insights, and actionable recommendations.")
        st.markdown("---")
        st.caption("Built with ❤️ using AI Technology")
    
    # Main dashboard area
    tab1, tab2, tab3 = st.tabs(["📊 Dashboard", "🔍 Detailed Analysis", "📝 Review List"])
    
    with tab1:
        # Infographic section
        st.markdown("## 📈 Key Metrics")
        create_infographic(df)
        
        # Quick report button
        col1, col2, col3 = st.columns([2, 1, 2])
        with col2:
            if st.button("📧 📊 Generate & Email Full Report", type="primary", use_container_width=True):
                if email:
                    send_immediate_report(email, reporter)
                else:
                    st.warning("⚠️ Please enter recipient email in the sidebar first")
        
        # Charts row
        col1, col2 = st.columns(2)
        
        with col1:
            sentiment_chart = create_sentiment_chart(df)
            st.plotly_chart(sentiment_chart, use_container_width=True)
        
        with col2:
            sarcasm_gauge = create_sarcasm_indicator(df)
            st.plotly_chart(sarcasm_gauge, use_container_width=True)
        
        # Timeline chart if available
        timeline = create_timeline_chart(df)
        if timeline:
            st.plotly_chart(timeline, use_container_width=True)
        
        # AI Insights section
        st.markdown("---")
        display_insights(insights)
        
        # Actionable recommendations
        st.markdown("---")
        st.markdown("## 🎯 Actionable Recommendations")
        
        # Create a summary of actions based on insights
        for idx, (problem, suggestion) in enumerate(zip(insights['problems'], insights['suggestions'])):
            with st.expander(f"📌 {problem}"):
                st.markdown(f"**Suggested Action:** {suggestion}")
                severity_level = insights.get('severity', ['Medium'])[idx] if idx < len(insights.get('severity', [])) else 'Medium'
                st.markdown(f"**Priority:** {severity_level}")
                if st.button(f"Mark as Resolved", key=f"resolve_{problem[:20]}"):
                    st.success("Marked as resolved! This will be tracked in future reports.")
    
    with tab2:
        st.markdown("## 🔍 Detailed Sentiment Analysis")
        
        # Filter options
        col1, col2 = st.columns(2)
        with col1:
            sentiment_filter = st.multiselect("Filter by Sentiment", 
                                             options=['Positive', 'Neutral', 'Negative'],
                                             default=['Positive', 'Neutral', 'Negative'])
        with col2:
            show_sarcasm_only = st.checkbox("Show only sarcastic reviews")
        
        # Filter data
        filtered_df = df[df['sentiment'].isin(sentiment_filter)]
        if show_sarcasm_only:
            filtered_df = filtered_df[filtered_df['sarcasm_detected'] == True]
        
        # Display detailed metrics
        st.markdown("### Sentiment Score Distribution")
        
        # Create box plot of sentiment scores
        scores_df = pd.DataFrame({
            'Negative Score': filtered_df['sentiment_negative_score'],
            'Neutral Score': filtered_df['sentiment_neutral_score'],
            'Positive Score': filtered_df['sentiment_positive_score']
        })
        
        fig = go.Figure()
        for col in scores_df.columns:
            fig.add_trace(go.Box(y=scores_df[col], name=col))
        
        fig.update_layout(title="Sentiment Score Distribution by Category",
                         height=400,
                         paper_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig, use_container_width=True)
        
        # Confidence distribution
        if 'confidence' in filtered_df.columns:
            confidence_counts = filtered_df['confidence'].value_counts()
            fig = px.bar(x=confidence_counts.index, y=confidence_counts.values,
                        title="Analysis Confidence Levels",
                        labels={'x': 'Confidence', 'y': 'Number of Reviews'},
                        color=confidence_counts.index,
                        color_discrete_map={'high': 'green', 'medium': 'orange', 'low': 'red'})
            st.plotly_chart(fig, use_container_width=True)
    
    with tab3:
        st.markdown("## 📝 All Reviews")
        
        # Search and filter
        search_term = st.text_input("🔍 Search reviews", placeholder="Enter keyword...")
        
        # Display reviews in a nice format
        display_df = filtered_df.copy()
        
        if search_term:
            display_df = display_df[display_df['full_text'].str.contains(search_term, case=False, na=False)]
        
        for idx, row in display_df.head(50).iterrows():
            sentiment_color = {
                'Positive': '🟢',
                'Neutral': '⚪',
                'Negative': '🔴'
            }.get(row['sentiment'], '⚪')
            
            sarcasm_badge = " 😏" if row['sarcasm_detected'] else ""
            
            with st.container():
                st.markdown(f"""
                <div style="background: white; padding: 1rem; border-radius: 10px; margin-bottom: 1rem; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <span style="font-size: 1.5rem;">{sentiment_color}</span>
                            <strong style="font-size: 1.1rem;">{row['sentiment']}</strong>
                            {sarcasm_badge}
                            <span style="color: #888; margin-left: 1rem;">Confidence: {row.get('confidence', 'medium').upper()}</span>
                        </div>
                        <small style="color: #888;">{row.get('date', 'Date not available')}</small>
                    </div>
                    <p style="margin-top: 0.5rem;">{row['full_text']}</p>
                </div>
                """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()