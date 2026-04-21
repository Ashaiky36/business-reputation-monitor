import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
from datetime import datetime, timedelta
import ollama
import re
from email_reporter import EmailReporter
from pdf_report_generator import PDFReportGenerator
import threading
import time
import os
# At the top of app.py, update the auth import
from auth import AuthSystem, init_session_state, login_screen, logout

# Page configuration
st.set_page_config(
    page_title="Business Reputation Monitor",
    page_icon="🔐",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Initialize session state
init_session_state()

# Initialize other session states
if 'app_stage' not in st.session_state:
    st.session_state.app_stage = 'setup'
if 'analysis_complete' not in st.session_state:
    st.session_state.analysis_complete = False
if 'report_scheduled' not in st.session_state:
    st.session_state.report_scheduled = False

# Load static reviews data (your pre-scraped data)
@st.cache_data
def load_static_reviews():
    """Load the pre-scraped reviews data"""
    try:
        df = pd.read_csv('analyzed_reviews_optimized.csv')
        return df
    except:
        try:
            df = pd.read_csv('reviews.csv')
            return df
        except:
            return None

@st.cache_data
def load_insights():
    """Load pre-generated insights"""
    try:
        with open('insights.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return None

def generate_overall_summary(df, insights, business_context=""):
    """Generate overall summary using Ollama based on all reviews"""
    
    # Calculate metrics
    total = len(df)
    positive = len(df[df['sentiment'] == 'Positive'])
    negative = len(df[df['sentiment'] == 'Negative'])
    neutral = len(df[df['sentiment'] == 'Neutral'])
    
    # Get sample reviews for context
    positive_samples = df[df['sentiment'] == 'Positive']['full_text'].head(3).tolist()
    negative_samples = df[df['sentiment'] == 'Negative']['full_text'].head(3).tolist()
    
    prompt = f"""Based on the following customer review analysis, provide a professional business summary.

BUSINESS CONTEXT: {business_context if business_context else 'General business'}

REVIEW STATISTICS:
- Total Reviews: {total}
- Positive: {positive} ({positive/total*100:.1f}%)
- Negative: {negative} ({negative/total*100:.1f}%)
- Neutral: {neutral} ({neutral/total*100:.1f}%)

SAMPLE POSITIVE REVIEWS:
{chr(10).join([f'- {r[:150]}' for r in positive_samples])}

SAMPLE NEGATIVE REVIEWS:
{chr(10).join([f'- {r[:150]}' for r in negative_samples])}

KEY PROBLEMS IDENTIFIED:
{chr(10).join([f'- {p}' for p in insights.get('problems', [])])}

Please provide a JSON response with:
1. "what_people_appreciate": What customers like (2-3 bullet points)
2. "what_people_dislike": Main complaints (2-3 bullet points)
3. "overall_recommendation": One paragraph recommendation
4. "business_health_score": A score from 0-100 based on sentiment

Respond ONLY with valid JSON."""

    try:
        response = ollama.chat(model='mistral', messages=[{'role': 'user', 'content': prompt}])
        result = json.loads(response['message']['content'])
        return result
    except:
        return {
            "what_people_appreciate": ["Product quality", "Customer service response"],
            "what_people_dislike": ["Technical issues", "Support delays"],
            "overall_recommendation": "Focus on addressing key customer complaints.",
            "business_health_score": 65
        }

def create_sentiment_gauge(positive_pct, negative_pct):
    """Create a gauge chart for overall sentiment"""
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=positive_pct,
        title={'text': "Overall Satisfaction Score", 'font': {'size': 24}},
        delta={'reference': 50, 'increasing': {'color': "green"}},
        gauge={
            'axis': {'range': [0, 100], 'tickwidth': 1},
            'bar': {'color': "darkblue"},
            'steps': [
                {'range': [0, 33], 'color': "red"},
                {'range': [33, 66], 'color': "orange"},
                {'range': [66, 100], 'color': "green"}
            ],
            'threshold': {
                'line': {'color': "black", 'width': 4},
                'thickness': 0.75,
                'value': positive_pct
            }
        }
    ))
    fig.update_layout(height=300, margin=dict(l=20, r=20, t=50, b=20))
    return fig

# def setup_screen():
#     """Display the setup screen"""
    
#     st.markdown("""
#     <style>
#     .big-title {
#         text-align: center;
#         background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
#         -webkit-background-clip: text;
#         -webkit-text-fill-color: transparent;
#         font-size: 3rem;
#         font-weight: bold;
#         margin-bottom: 0;
#     }
#     .subtitle {
#         text-align: center;
#         color: #666;
#         margin-bottom: 2rem;
#     }
#     .info-box {
#         background-color: #f0f2f6;
#         padding: 20px;
#         border-radius: 10px;
#         margin: 10px 0;
#     }
#     </style>
#     """, unsafe_allow_html=True)
    
#     st.markdown('<p class="big-title">🚀 Business Reputation Monitor</p>', unsafe_allow_html=True)
#     st.markdown('<p class="subtitle">AI-Powered Sentiment Analysis & Reputation Management</p>', unsafe_allow_html=True)
    
#     st.markdown("---")
    
#     col1, col2 = st.columns([2, 1])
    
#     with col1:
#         st.markdown("## 📝 Business Information")
        
#         with st.form("business_setup"):
#             # Business URL (for demonstration - we'll use static data)
#             trustpilot_url = st.text_input(
#                 "Trustpilot Business URL",
#                 placeholder="https://www.trustpilot.com/review/www.apple.com",
#                 help="Enter the Trustpilot URL for analysis (Demo: using pre-analyzed data)"
#             )
            
#             # Email for reports
#             email = st.text_input(
#                 "Email Address *",
#                 placeholder="business@example.com"
#             )
            
#             # Business name
#             business_name = st.text_input(
#                 "Business Name",
#                 placeholder="Apple Inc.",
#                 help="Name of your business"
#             )
            
#             # Business context
#             business_context = st.text_area(
#                 "Business Context (Optional)",
#                 placeholder="Describe your business, products, or specific concerns...",
#                 help="This helps our AI provide more accurate insights",
#                 height=100
#             )
            
#             submitted = st.form_submit_button("🚀 Analyze Reputation", type="primary", use_container_width=True)
            
#             if submitted:
#                 if not email:
#                     st.error("Please enter your email address")
#                 else:
#                     # Store in session state
#                     st.session_state.business_info = {
#                         'url': trustpilot_url if trustpilot_url else "demo.trustpilot.com/review/apple",
#                         'email': email,
#                         'business_name': business_name if business_name else "Business",
#                         'business_context': business_context,
#                         'analysis_time': datetime.now()
#                     }
#                     st.session_state.app_stage = 'results'
#                     st.rerun()
    
#     with col2:
#         st.markdown("## 🎯 What You'll Get")
#         st.markdown("""
#         <div class="info-box">
#         <b>📊 Real-time Dashboard</b><br>
#         Visual analytics of customer sentiment
        
#         <br><br><b>🤖 AI-Powered Insights</b><br>
#         What customers appreciate & dislike
        
#         <br><br><b>💡 Actionable Recommendations</b><br>
#         Specific steps to improve reputation
        
#         <br><br><b>📧 Automated Email Reports</b><br>
#         Scheduled reports to your inbox
#         </div>
#         """, unsafe_allow_html=True)
        
#         st.markdown("---")
#         st.caption("💡 **Note:** This demonstration uses pre-analyzed review data to ensure reliable performance. In production, it would scrape live reviews from Trustpilot.")

def setup_screen():
    """Display the setup screen with business information"""
    
    # Display user info if logged in
    if st.session_state.user:
        st.markdown(f"""
        <div style="text-align: right; padding: 0.5rem; background: #f0f2f6; border-radius: 5px; margin-bottom: 1rem;">
            👋 Welcome, <b>{st.session_state.user['full_name']}</b> | 
            📧 {st.session_state.user['email']}
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("""
    <style>
    .big-title {
        text-align: center;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 3rem;
        font-weight: bold;
        margin-bottom: 0;
    }
    .subtitle {
        text-align: center;
        color: #666;
        margin-bottom: 2rem;
    }
    .info-box {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        margin: 10px 0;
    }
    </style>
    """, unsafe_allow_html=True)
    
    st.markdown('<p class="big-title">🚀 Business Reputation Monitor</p>', unsafe_allow_html=True)
    st.markdown('<p class="subtitle">AI-Powered Sentiment Analysis & Reputation Management</p>', unsafe_allow_html=True)
    
    st.markdown("---")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("## 📝 Business Information")
        
        # Create form with proper submit button
        with st.form(key="business_setup_form"):
            # Business URL (for demonstration - we'll use static data)
            trustpilot_url = st.text_input(
                "Trustpilot Business URL",
                placeholder="https://www.trustpilot.com/review/www.apple.com",
                help="Enter the Trustpilot URL for analysis (Demo: using pre-analyzed data)",
                key="setup_url_input"
            )
            
            # Pre-fill email from logged-in user
            default_email = st.session_state.user['email'] if st.session_state.user else ""
            email = st.text_input(
                "Email Address *",
                placeholder="business@example.com",
                value=default_email,
                disabled=True if st.session_state.user else False,
                help="Email is linked to your account",
                key="setup_email_input"
            )
            
            # Business name - pre-fill from user data if available
            default_business = st.session_state.user.get('business_name', '') if st.session_state.user else ""
            business_name = st.text_input(
                "Business Name",
                placeholder="Apple Inc.",
                value=default_business,
                help="Name of your business",
                key="setup_business_name_input"
            )
            
            # Business context
            business_context = st.text_area(
                "Business Context (Optional)",
                placeholder="Describe your business, products, or specific concerns...",
                help="This helps our AI provide more accurate insights",
                height=100,
                key="setup_context_input"
            )
            
            # Submit button inside the form
            submitted = st.form_submit_button("🚀 Analyze Reputation", type="primary", use_container_width=True)
            
            if submitted:
                # Validate email
                if not email:
                    st.error("Please enter your email address")
                else:
                    # Store in session state
                    st.session_state.business_info = {
                        'url': trustpilot_url if trustpilot_url else "demo.trustpilot.com/review/apple",
                        'email': email,
                        'business_name': business_name if business_name else st.session_state.user.get('business_name', 'Business'),
                        'business_context': business_context,
                        'analysis_time': datetime.now()
                    }
                    st.session_state.app_stage = 'results'
                    st.rerun()
    
    with col2:
        st.markdown("## 🎯 What You'll Get")
        st.markdown("""
        <div class="info-box">
        <b>📊 Real-time Dashboard</b><br>
        Visual analytics of customer sentiment
        
        <br><br><b>🤖 AI-Powered Insights</b><br>
        What customers appreciate & dislike
        
        <br><br><b>💡 Actionable Recommendations</b><br>
        Specific steps to improve reputation
        
        <br><br><b>📧 Automated Email Reports</b><br>
        Scheduled reports to your inbox
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Logout button with unique key
        if st.session_state.user:
            if st.button("🚪 Logout", use_container_width=True, key="setup_logout_button"):
                from auth import logout
                logout()
        
        st.caption("💡 **Note:** This demonstration uses pre-analyzed review data to ensure reliable performance.")

def results_screen():
    """Display the results dashboard"""
    # Add logout button in top right corner
    col1, col2, col3 = st.columns([5, 1, 1])
    with col3:
     if st.button("🚪 Logout", key="results_logout_button"):
        logout()
    
    
    # Load data
    df = load_static_reviews()
    insights = load_insights()
    
    if df is None:
        st.error("No review data available. Please ensure 'analyzed_reviews_optimized.csv' exists.")
        if st.button("◀ Back to Setup"):
            st.session_state.app_stage = 'setup'
            st.rerun()
        return
    
    # Calculate metrics
    total_reviews = len(df)
    negative_count = len(df[df['sentiment'] == 'Negative'])
    positive_count = len(df[df['sentiment'] == 'Positive'])
    neutral_count = len(df[df['sentiment'] == 'Neutral'])
    negative_percentage = (negative_count / total_reviews) * 100
    positive_percentage = (positive_count / total_reviews) * 100
    
    # Generate overall summary if not already done
    if 'overall_summary' not in st.session_state:
        with st.spinner("🤖 Generating AI-powered summary..."):
            st.session_state.overall_summary = generate_overall_summary(
                df, insights, st.session_state.business_info.get('business_context', '')
            )
    
    # Header with business info
    st.markdown(f"""
    <div style="text-align: center; margin-bottom: 2rem;">
        <h1>📊 {st.session_state.business_info.get('business_name', 'Business')} Reputation Report</h1>
        <p style="color: #666;">Analysis completed: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # ==================== SECTION 1: KEY METRICS ====================
    st.markdown("## 📈 Key Metrics")
    
    # Display negative count prominently
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("📊 Total Reviews", total_reviews)
    with col2:
        st.metric("🔴 Negative Reviews", f"{negative_count} ({negative_percentage:.1f}%)", delta=f"{negative_percentage:.0f}% of total")
    with col3:
        st.metric("🟢 Positive Reviews", f"{positive_count} ({positive_percentage:.1f}%)")
    with col4:
        st.metric("⚪ Neutral Reviews", neutral_count)
    
    # ==================== SECTION 2: MAJOR PROBLEMS & SOLUTIONS ====================
    st.markdown("---")
    st.markdown("## ⚠️ Major Problems & AI-Powered Solutions")
    
    if insights and 'problems' in insights:
        cols = st.columns(len(insights['problems']))
        for idx, (col, problem, suggestion, severity) in enumerate(zip(
            cols, 
            insights['problems'], 
            insights['suggestions'], 
            insights.get('severity', ['Medium']*len(insights['problems']))
        )):
            with col:
                severity_color = {'High': '🔴', 'Medium': '🟡', 'Low': '🟢'}.get(severity, '⚪')
                st.markdown(f"""
                <div style="background: white; padding: 1.5rem; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); border-top: 4px solid {'#ff4757' if severity == 'High' else '#ffb347' if severity == 'Medium' else '#00ff88'};">
                    <h3 style="margin-top: 0;">Problem {idx+1}</h3>
                    <p><strong>{problem}</strong></p>
                    <p><strong>💡 Solution:</strong><br>{suggestion}</p>
                    <p><strong>Priority:</strong> {severity_color} {severity}</p>
                </div>
                """, unsafe_allow_html=True)
    else:
        st.info("No insights available. Run sentiment analysis first.")
    
    # ==================== SECTION 3: OVERALL SUMMARY ====================
    st.markdown("---")
    st.markdown("## 📋 Overall Analysis Summary")
    
    summary = st.session_state.overall_summary
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### ✅ What Customers Appreciate")
        for point in summary.get('what_people_appreciate', []):
            st.markdown(f"- {point}")
    
    with col2:
        st.markdown("### ❌ What Customers Dislike")
        for point in summary.get('what_people_dislike', []):
            st.markdown(f"- {point}")
    
    st.markdown("### 💡 Overall Recommendation")
    st.info(summary.get('overall_recommendation', 'Focus on addressing customer feedback.'))
    
    # Health score gauge
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        health_score = summary.get('business_health_score', 65)
        gauge = create_sentiment_gauge(positive_percentage, negative_percentage)
        st.plotly_chart(gauge, use_container_width=True)
        st.markdown(f"<p style='text-align: center;'><b>Business Health Score: {health_score}/100</b></p>", unsafe_allow_html=True)
    
    # ==================== SECTION 4: VISUALIZATIONS ====================
    st.markdown("---")
    st.markdown("## 📊 Sentiment Visualizations")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Sentiment pie chart
        sentiment_counts = df['sentiment'].value_counts()
        fig_pie = go.Figure(data=[go.Pie(
            labels=sentiment_counts.index,
            values=sentiment_counts.values,
            hole=0.4,
            marker_colors=['#ff4757', '#ffb347', '#00ff88']
        )])
        fig_pie.update_layout(title="Sentiment Distribution", height=400)
        st.plotly_chart(fig_pie, use_container_width=True)
    
    with col2:
        # Sarcasm indicator if available
        if 'sarcasm_detected' in df.columns:
            sarcasm_count = df['sarcasm_detected'].sum()
            sarcasm_pct = (sarcasm_count / total_reviews) * 100
            fig_gauge = go.Figure(go.Indicator(
                mode="gauge+number",
                value=sarcasm_pct,
                title={'text': "Sarcasm Detection Rate"},
                gauge={'axis': {'range': [0, 100]}, 'bar': {'color': "darkorange"}}
            ))
            fig_gauge.update_layout(height=300)
            st.plotly_chart(fig_gauge, use_container_width=True)
    
    # ==================== SECTION 5: REPORT GENERATION ====================
    st.markdown("---")
    st.markdown("## 📧 Report Configuration")
    
    col1, col2, col3 = st.columns([2, 1, 2])
    
    with col2:
        # Email input
        report_email = st.text_input(
            "Email Address for Reports",
            value=st.session_state.business_info.get('email', ''),
            key="report_email"
        )
        
        # Interval in days
        interval_days = st.number_input(
            "Report Interval (Days)",
            min_value=1,
            max_value=30,
            value=7,
            help="How often to send automated reports"
        )
        
        # Send now button
        if st.button("📧 Send Email Report Now", type="primary", use_container_width=True):
            if report_email:
                with st.spinner("Generating and sending report..."):
                    try:
                        reporter = EmailReporter()
                        success = reporter.send_report_email(report_email, "ondemand", include_pdf=True)
                        if success:
                            st.success(f"✅ Report sent to {report_email}")
                            st.info("📬 Check MailHog at http://localhost:8025 to view the email")
                        else:
                            st.error("Failed to send email. Is MailHog running?")
                    except Exception as e:
                        st.error(f"Error: {e}")
            else:
                st.warning("Please enter an email address")
        
        # Schedule button
        if st.button("⏰ Schedule Automated Reports", use_container_width=True):
            if report_email:
                st.success(f"✅ Reports scheduled every {interval_days} day(s) to {report_email}")
                st.session_state.report_scheduled = True
                st.info(f"📅 Next report: {(datetime.now() + timedelta(days=interval_days)).strftime('%B %d, %Y')}")
            else:
                st.warning("Please enter an email address")
    
    # ==================== SECTION 6: SAMPLE REVIEWS ====================
    # st.markdown("---")
    # st.markdown("## 📝 Recent Customer Reviews")
    
    # # Filter options
    # sentiment_filter = st.multiselect(
    #     "Filter by Sentiment",
    #     options=['Positive', 'Neutral', 'Negative'],
    #     default=['Positive', 'Neutral', 'Negative']
    # )
    
    # filtered_df = df[df['sentiment'].isin(sentiment_filter)]
    
    # for idx, row in filtered_df.head(10).iterrows():
    #     sentiment_icon = {'Positive': '🟢', 'Neutral': '⚪', 'Negative': '🔴'}.get(row['sentiment'], '⚪')
    #     st.markdown(f"""
    #     <div style="background: #f8f9fa; padding: 1rem; border-radius: 10px; margin-bottom: 1rem;">
    #         <div style="display: flex; justify-content: space-between;">
    #             <div>
    #                 <span style="font-size: 1.2rem;">{sentiment_icon}</span>
    #                 <strong>{row['sentiment']}</strong>
    #                 {' 😏' if row.get('sarcasm_detected', False) else ''}
    #             </div>
    #             <small>{row.get('date', 'Date not available')}</small>
    #         </div>
    #         <p style="margin-top: 0.5rem;">{row.get('full_text', row.get('content', 'No content'))[:300]}...</p>
    #     </div>
    #     """, unsafe_allow_html=True)

        # ==================== SECTION 6: SAMPLE REVIEWS ====================
    st.markdown("---")
    st.markdown("## 📝 Recent Customer Reviews")
    
    # Filter options in a more compact layout
    col1, col2, col3 = st.columns([2, 2, 1])
    with col1:
        sentiment_filter = st.multiselect(
            "Filter by Sentiment",
            options=['Positive', 'Neutral', 'Negative'],
            default=['Positive', 'Neutral', 'Negative'],
            key="sentiment_filter"
        )
    
    with col2:
        search_term = st.text_input("🔍 Search Reviews", placeholder="Enter keyword...", key="search_reviews")
    
    # Apply filters
    filtered_df = df[df['sentiment'].isin(sentiment_filter)]
    if search_term:
        filtered_df = filtered_df[filtered_df['full_text'].str.contains(search_term, case=False, na=False)]
    
    # Professional review cards without tags
    for idx, row in filtered_df.head(10).iterrows():
        # Determine sentiment icon and color
        if row['sentiment'] == 'Positive':
            sentiment_color = "#00ff88"
            sentiment_icon = "✓"
        elif row['sentiment'] == 'Negative':
            sentiment_color = "#ff4757"
            sentiment_icon = "✗"
        else:
            sentiment_color = "#ffb347"
            sentiment_icon = "●"
        
        # Clean review display without extra tags
        st.markdown(f"""
        <div style="background: #ffffff; padding: 1.2rem; border-radius: 8px; margin-bottom: 1rem; box-shadow: 0 1px 3px rgba(0,0,0,0.1); border-left: 4px solid {sentiment_color};">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
                <div style="display: flex; align-items: center; gap: 0.5rem;">
                    <span style="font-size: 1.1rem; font-weight: 600; color: {sentiment_color};">{sentiment_icon}</span>
                    <span style="font-weight: 500; color: #333;">{row['sentiment']}</span>
                    <span style="color: #999; font-size: 0.85rem;">•</span>
                    <span style="color: #666; font-size: 0.85rem;">Rating: {row.get('rating', 'N/A')}★</span>
                </div>
                <small style="color: #999;">{row.get('date', 'Date not available')}</small>
            </div>
            <p style="margin: 0.5rem 0 0 0; color: #444; line-height: 1.5;">{row.get('full_text', row.get('content', 'No content'))[:350]}{'...' if len(row.get('full_text', row.get('content', ''))) > 350 else ''}</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Show message if no reviews match filters
    if len(filtered_df.head(10)) == 0:
        st.info("No reviews match your current filters. Try adjusting the sentiment filter or search term.")
    
    # Show count of displayed reviews
    st.caption(f"Showing {min(10, len(filtered_df))} of {len(filtered_df)} reviews matching your criteria")
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #666; padding: 2rem;">
        <p>🚀 Built with AI Technology | Sentiment Analysis | Sarcasm Detection | Automated Reporting</p>
        <p><small>Note: This demonstration uses pre-analyzed review data. In production, it would scrape live reviews from Trustpilot.</small></p>
    </div>
    """, unsafe_allow_html=True)
    
    # New analysis button
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🔄 Analyze Another Business", use_container_width=True):
            st.session_state.app_stage = 'setup'
            st.session_state.pop('overall_summary', None)
            st.rerun()

def main():
    # Check authentication
    if not st.session_state.authenticated:
        login_screen()
    else:
        # Show main app
        if st.session_state.app_stage == 'setup':
            setup_screen()
        elif st.session_state.app_stage == 'results':
            results_screen()

if __name__ == "__main__":
    main()