# import streamlit as st
# import pandas as pd
# import plotly.express as px
# import plotly.graph_objects as go
# import json
# from datetime import datetime, timedelta
# import ollama
# import re
# from email_reporter import EmailReporter
# from pdf_report_generator import PDFReportGenerator
# import threading
# import time
# import os
# # At the top of app.py, update the auth import
# from auth import AuthSystem, init_session_state, login_screen, logout

# # Page configuration
# st.set_page_config(
#     page_title="Business Reputation Monitor",
#     page_icon="🔐",
#     layout="wide",
#     initial_sidebar_state="collapsed"
# )

# # Initialize session state
# init_session_state()

# # Initialize other session states
# if 'app_stage' not in st.session_state:
#     st.session_state.app_stage = 'setup'
# if 'analysis_complete' not in st.session_state:
#     st.session_state.analysis_complete = False
# if 'report_scheduled' not in st.session_state:
#     st.session_state.report_scheduled = False

# # Load static reviews data (your pre-scraped data)
# @st.cache_data
# def load_static_reviews():
#     """Load the pre-scraped reviews data"""
#     try:
#         df = pd.read_csv('analyzed_reviews_optimized.csv')
#         return df
#     except:
#         try:
#             df = pd.read_csv('reviews.csv')
#             return df
#         except:
#             return None

# @st.cache_data
# def load_insights():
#     """Load pre-generated insights"""
#     try:
#         with open('insights.json', 'r', encoding='utf-8') as f:
#             return json.load(f)
#     except:
#         return None

# def generate_overall_summary(df, insights, business_context=""):
#     """Generate overall summary using Ollama based on all reviews"""
    
#     # Calculate metrics
#     total = len(df)
#     positive = len(df[df['sentiment'] == 'Positive'])
#     negative = len(df[df['sentiment'] == 'Negative'])
#     neutral = len(df[df['sentiment'] == 'Neutral'])
    
#     # Get sample reviews for context
#     positive_samples = df[df['sentiment'] == 'Positive']['full_text'].head(3).tolist()
#     negative_samples = df[df['sentiment'] == 'Negative']['full_text'].head(3).tolist()
    
#     prompt = f"""Based on the following customer review analysis, provide a professional business summary.

# BUSINESS CONTEXT: {business_context if business_context else 'General business'}

# REVIEW STATISTICS:
# - Total Reviews: {total}
# - Positive: {positive} ({positive/total*100:.1f}%)
# - Negative: {negative} ({negative/total*100:.1f}%)
# - Neutral: {neutral} ({neutral/total*100:.1f}%)

# SAMPLE POSITIVE REVIEWS:
# {chr(10).join([f'- {r[:150]}' for r in positive_samples])}

# SAMPLE NEGATIVE REVIEWS:
# {chr(10).join([f'- {r[:150]}' for r in negative_samples])}

# KEY PROBLEMS IDENTIFIED:
# {chr(10).join([f'- {p}' for p in insights.get('problems', [])])}

# Please provide a JSON response with:
# 1. "what_people_appreciate": What customers like (2-3 bullet points)
# 2. "what_people_dislike": Main complaints (2-3 bullet points)
# 3. "overall_recommendation": One paragraph recommendation
# 4. "business_health_score": A score from 0-100 based on sentiment

# Respond ONLY with valid JSON."""

#     try:
#         response = ollama.chat(model='mistral', messages=[{'role': 'user', 'content': prompt}])
#         result = json.loads(response['message']['content'])
#         return result
#     except:
#         return {
#             "what_people_appreciate": ["Product quality", "Customer service response"],
#             "what_people_dislike": ["Technical issues", "Support delays"],
#             "overall_recommendation": "Focus on addressing key customer complaints.",
#             "business_health_score": 65
#         }

# def create_sentiment_gauge(positive_pct, negative_pct):
#     """Create a gauge chart for overall sentiment"""
#     fig = go.Figure(go.Indicator(
#         mode="gauge+number+delta",
#         value=positive_pct,
#         title={'text': "Overall Satisfaction Score", 'font': {'size': 24}},
#         delta={'reference': 50, 'increasing': {'color': "green"}},
#         gauge={
#             'axis': {'range': [0, 100], 'tickwidth': 1},
#             'bar': {'color': "darkblue"},
#             'steps': [
#                 {'range': [0, 33], 'color': "red"},
#                 {'range': [33, 66], 'color': "orange"},
#                 {'range': [66, 100], 'color': "green"}
#             ],
#             'threshold': {
#                 'line': {'color': "black", 'width': 4},
#                 'thickness': 0.75,
#                 'value': positive_pct
#             }
#         }
#     ))
#     fig.update_layout(height=300, margin=dict(l=20, r=20, t=50, b=20))
#     return fig

# # def setup_screen():
# #     """Display the setup screen"""
    
# #     st.markdown("""
# #     <style>
# #     .big-title {
# #         text-align: center;
# #         background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
# #         -webkit-background-clip: text;
# #         -webkit-text-fill-color: transparent;
# #         font-size: 3rem;
# #         font-weight: bold;
# #         margin-bottom: 0;
# #     }
# #     .subtitle {
# #         text-align: center;
# #         color: #666;
# #         margin-bottom: 2rem;
# #     }
# #     .info-box {
# #         background-color: #f0f2f6;
# #         padding: 20px;
# #         border-radius: 10px;
# #         margin: 10px 0;
# #     }
# #     </style>
# #     """, unsafe_allow_html=True)
    
# #     st.markdown('<p class="big-title">🚀 Business Reputation Monitor</p>', unsafe_allow_html=True)
# #     st.markdown('<p class="subtitle">AI-Powered Sentiment Analysis & Reputation Management</p>', unsafe_allow_html=True)
    
# #     st.markdown("---")
    
# #     col1, col2 = st.columns([2, 1])
    
# #     with col1:
# #         st.markdown("## 📝 Business Information")
        
# #         with st.form("business_setup"):
# #             # Business URL (for demonstration - we'll use static data)
# #             trustpilot_url = st.text_input(
# #                 "Trustpilot Business URL",
# #                 placeholder="https://www.trustpilot.com/review/www.apple.com",
# #                 help="Enter the Trustpilot URL for analysis (Demo: using pre-analyzed data)"
# #             )
            
# #             # Email for reports
# #             email = st.text_input(
# #                 "Email Address *",
# #                 placeholder="business@example.com"
# #             )
            
# #             # Business name
# #             business_name = st.text_input(
# #                 "Business Name",
# #                 placeholder="Apple Inc.",
# #                 help="Name of your business"
# #             )
            
# #             # Business context
# #             business_context = st.text_area(
# #                 "Business Context (Optional)",
# #                 placeholder="Describe your business, products, or specific concerns...",
# #                 help="This helps our AI provide more accurate insights",
# #                 height=100
# #             )
            
# #             submitted = st.form_submit_button("🚀 Analyze Reputation", type="primary", use_container_width=True)
            
# #             if submitted:
# #                 if not email:
# #                     st.error("Please enter your email address")
# #                 else:
# #                     # Store in session state
# #                     st.session_state.business_info = {
# #                         'url': trustpilot_url if trustpilot_url else "demo.trustpilot.com/review/apple",
# #                         'email': email,
# #                         'business_name': business_name if business_name else "Business",
# #                         'business_context': business_context,
# #                         'analysis_time': datetime.now()
# #                     }
# #                     st.session_state.app_stage = 'results'
# #                     st.rerun()
    
# #     with col2:
# #         st.markdown("## 🎯 What You'll Get")
# #         st.markdown("""
# #         <div class="info-box">
# #         <b>📊 Real-time Dashboard</b><br>
# #         Visual analytics of customer sentiment
        
# #         <br><br><b>🤖 AI-Powered Insights</b><br>
# #         What customers appreciate & dislike
        
# #         <br><br><b>💡 Actionable Recommendations</b><br>
# #         Specific steps to improve reputation
        
# #         <br><br><b>📧 Automated Email Reports</b><br>
# #         Scheduled reports to your inbox
# #         </div>
# #         """, unsafe_allow_html=True)
        
# #         st.markdown("---")
# #         st.caption("💡 **Note:** This demonstration uses pre-analyzed review data to ensure reliable performance. In production, it would scrape live reviews from Trustpilot.")

# def setup_screen():
#     """Display the setup screen with business information"""
    
#     # Display user info if logged in
#     if st.session_state.user:
#         st.markdown(f"""
#         <div style="text-align: right; padding: 0.5rem; background: #f0f2f6; border-radius: 5px; margin-bottom: 1rem;">
#             👋 Welcome, <b>{st.session_state.user['full_name']}</b> | 
#             📧 {st.session_state.user['email']}
#         </div>
#         """, unsafe_allow_html=True)
    
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
        
#         # Create form with proper submit button
#         with st.form(key="business_setup_form"):
#             # Business URL (for demonstration - we'll use static data)
#             trustpilot_url = st.text_input(
#                 "Trustpilot Business URL",
#                 placeholder="https://www.trustpilot.com/review/www.apple.com",
#                 help="Enter the Trustpilot URL for analysis (Demo: using pre-analyzed data)",
#                 key="setup_url_input"
#             )
            
#             # Pre-fill email from logged-in user
#             default_email = st.session_state.user['email'] if st.session_state.user else ""
#             email = st.text_input(
#                 "Email Address *",
#                 placeholder="business@example.com",
#                 value=default_email,
#                 disabled=True if st.session_state.user else False,
#                 help="Email is linked to your account",
#                 key="setup_email_input"
#             )
            
#             # Business name - pre-fill from user data if available
#             default_business = st.session_state.user.get('business_name', '') if st.session_state.user else ""
#             business_name = st.text_input(
#                 "Business Name",
#                 placeholder="Apple Inc.",
#                 value=default_business,
#                 help="Name of your business",
#                 key="setup_business_name_input"
#             )
            
#             # Business context
#             business_context = st.text_area(
#                 "Business Context (Optional)",
#                 placeholder="Describe your business, products, or specific concerns...",
#                 help="This helps our AI provide more accurate insights",
#                 height=100,
#                 key="setup_context_input"
#             )
            
#             # Submit button inside the form
#             submitted = st.form_submit_button("🚀 Analyze Reputation", type="primary", use_container_width=True)
            
#             if submitted:
#                 # Validate email
#                 if not email:
#                     st.error("Please enter your email address")
#                 else:
#                     # Store in session state
#                     st.session_state.business_info = {
#                         'url': trustpilot_url if trustpilot_url else "demo.trustpilot.com/review/apple",
#                         'email': email,
#                         'business_name': business_name if business_name else st.session_state.user.get('business_name', 'Business'),
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
        
#         # Logout button with unique key
#         if st.session_state.user:
#             if st.button("🚪 Logout", use_container_width=True, key="setup_logout_button"):
#                 from auth import logout
#                 logout()
        
#         st.caption("💡 **Note:** This demonstration uses pre-analyzed review data to ensure reliable performance.")

# def results_screen():
#     """Display the results dashboard"""
#     # Add logout button in top right corner
#     col1, col2, col3 = st.columns([5, 1, 1])
#     with col3:
#      if st.button("🚪 Logout", key="results_logout_button"):
#         logout()
    
    
#     # Load data
#     df = load_static_reviews()
#     insights = load_insights()
    
#     if df is None:
#         st.error("No review data available. Please ensure 'analyzed_reviews_optimized.csv' exists.")
#         if st.button("◀ Back to Setup"):
#             st.session_state.app_stage = 'setup'
#             st.rerun()
#         return
    
#     # Calculate metrics
#     total_reviews = len(df)
#     negative_count = len(df[df['sentiment'] == 'Negative'])
#     positive_count = len(df[df['sentiment'] == 'Positive'])
#     neutral_count = len(df[df['sentiment'] == 'Neutral'])
#     negative_percentage = (negative_count / total_reviews) * 100
#     positive_percentage = (positive_count / total_reviews) * 100
    
#     # Generate overall summary if not already done
#     if 'overall_summary' not in st.session_state:
#         with st.spinner("🤖 Generating AI-powered summary..."):
#             st.session_state.overall_summary = generate_overall_summary(
#                 df, insights, st.session_state.business_info.get('business_context', '')
#             )
    
#     # Header with business info
#     st.markdown(f"""
#     <div style="text-align: center; margin-bottom: 2rem;">
#         <h1>📊 {st.session_state.business_info.get('business_name', 'Business')} Reputation Report</h1>
#         <p style="color: #666;">Analysis completed: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}</p>
#     </div>
#     """, unsafe_allow_html=True)
    
#     st.markdown("---")
    
#     # ==================== SECTION 1: KEY METRICS ====================
#     st.markdown("## 📈 Key Metrics")
    
#     # Display negative count prominently
#     col1, col2, col3, col4 = st.columns(4)
#     with col1:
#         st.metric("📊 Total Reviews", total_reviews)
#     with col2:
#         st.metric("🔴 Negative Reviews", f"{negative_count} ({negative_percentage:.1f}%)", delta=f"{negative_percentage:.0f}% of total")
#     with col3:
#         st.metric("🟢 Positive Reviews", f"{positive_count} ({positive_percentage:.1f}%)")
#     with col4:
#         st.metric("⚪ Neutral Reviews", neutral_count)
    
#     # ==================== SECTION 2: MAJOR PROBLEMS & SOLUTIONS ====================
#     st.markdown("---")
#     st.markdown("## ⚠️ Major Problems & AI-Powered Solutions")
    
#     if insights and 'problems' in insights:
#         cols = st.columns(len(insights['problems']))
#         for idx, (col, problem, suggestion, severity) in enumerate(zip(
#             cols, 
#             insights['problems'], 
#             insights['suggestions'], 
#             insights.get('severity', ['Medium']*len(insights['problems']))
#         )):
#             with col:
#                 severity_color = {'High': '🔴', 'Medium': '🟡', 'Low': '🟢'}.get(severity, '⚪')
#                 st.markdown(f"""
#                 <div style="background: white; padding: 1.5rem; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); border-top: 4px solid {'#ff4757' if severity == 'High' else '#ffb347' if severity == 'Medium' else '#00ff88'};">
#                     <h3 style="margin-top: 0;">Problem {idx+1}</h3>
#                     <p><strong>{problem}</strong></p>
#                     <p><strong>💡 Solution:</strong><br>{suggestion}</p>
#                     <p><strong>Priority:</strong> {severity_color} {severity}</p>
#                 </div>
#                 """, unsafe_allow_html=True)
#     else:
#         st.info("No insights available. Run sentiment analysis first.")
    
#     # ==================== SECTION 3: OVERALL SUMMARY ====================
#     st.markdown("---")
#     st.markdown("## 📋 Overall Analysis Summary")
    
#     summary = st.session_state.overall_summary
    
#     col1, col2 = st.columns(2)
#     with col1:
#         st.markdown("### ✅ What Customers Appreciate")
#         for point in summary.get('what_people_appreciate', []):
#             st.markdown(f"- {point}")
    
#     with col2:
#         st.markdown("### ❌ What Customers Dislike")
#         for point in summary.get('what_people_dislike', []):
#             st.markdown(f"- {point}")
    
#     st.markdown("### 💡 Overall Recommendation")
#     st.info(summary.get('overall_recommendation', 'Focus on addressing customer feedback.'))
    
#     # Health score gauge
#     col1, col2, col3 = st.columns([1, 2, 1])
#     with col2:
#         health_score = summary.get('business_health_score', 65)
#         gauge = create_sentiment_gauge(positive_percentage, negative_percentage)
#         st.plotly_chart(gauge, use_container_width=True)
#         st.markdown(f"<p style='text-align: center;'><b>Business Health Score: {health_score}/100</b></p>", unsafe_allow_html=True)
    
#     # ==================== SECTION 4: VISUALIZATIONS ====================
#     st.markdown("---")
#     st.markdown("## 📊 Sentiment Visualizations")
    
#     col1, col2 = st.columns(2)
    
#     with col1:
#         # Sentiment pie chart
#         sentiment_counts = df['sentiment'].value_counts()
#         fig_pie = go.Figure(data=[go.Pie(
#             labels=sentiment_counts.index,
#             values=sentiment_counts.values,
#             hole=0.4,
#             marker_colors=['#ff4757', '#ffb347', '#00ff88']
#         )])
#         fig_pie.update_layout(title="Sentiment Distribution", height=400)
#         st.plotly_chart(fig_pie, use_container_width=True)
    
#     with col2:
#         # Sarcasm indicator if available
#         if 'sarcasm_detected' in df.columns:
#             sarcasm_count = df['sarcasm_detected'].sum()
#             sarcasm_pct = (sarcasm_count / total_reviews) * 100
#             fig_gauge = go.Figure(go.Indicator(
#                 mode="gauge+number",
#                 value=sarcasm_pct,
#                 title={'text': "Sarcasm Detection Rate"},
#                 gauge={'axis': {'range': [0, 100]}, 'bar': {'color': "darkorange"}}
#             ))
#             fig_gauge.update_layout(height=300)
#             st.plotly_chart(fig_gauge, use_container_width=True)
    
#     # ==================== SECTION 5: REPORT GENERATION ====================
#     st.markdown("---")
#     st.markdown("## 📧 Report Configuration")
    
#     col1, col2, col3 = st.columns([2, 1, 2])
    
#     with col2:
#         # Email input
#         report_email = st.text_input(
#             "Email Address for Reports",
#             value=st.session_state.business_info.get('email', ''),
#             key="report_email"
#         )
        
#         # Interval in days
#         interval_days = st.number_input(
#             "Report Interval (Days)",
#             min_value=1,
#             max_value=30,
#             value=7,
#             help="How often to send automated reports"
#         )
        
#         # Send now button
#         if st.button("📧 Send Email Report Now", type="primary", use_container_width=True):
#             if report_email:
#                 with st.spinner("Generating and sending report..."):
#                     try:
#                         reporter = EmailReporter()
#                         success = reporter.send_report_email(report_email, "ondemand", include_pdf=True)
#                         if success:
#                             st.success(f"✅ Report sent to {report_email}")
#                             st.info("📬 Check MailHog at http://localhost:8025 to view the email")
#                         else:
#                             st.error("Failed to send email. Is MailHog running?")
#                     except Exception as e:
#                         st.error(f"Error: {e}")
#             else:
#                 st.warning("Please enter an email address")
        
#         # Schedule button
#         if st.button("⏰ Schedule Automated Reports", use_container_width=True):
#             if report_email:
#                 st.success(f"✅ Reports scheduled every {interval_days} day(s) to {report_email}")
#                 st.session_state.report_scheduled = True
#                 st.info(f"📅 Next report: {(datetime.now() + timedelta(days=interval_days)).strftime('%B %d, %Y')}")
#             else:
#                 st.warning("Please enter an email address")
    
#     # ==================== SECTION 6: SAMPLE REVIEWS ====================
#     # st.markdown("---")
#     # st.markdown("## 📝 Recent Customer Reviews")
    
#     # # Filter options
#     # sentiment_filter = st.multiselect(
#     #     "Filter by Sentiment",
#     #     options=['Positive', 'Neutral', 'Negative'],
#     #     default=['Positive', 'Neutral', 'Negative']
#     # )
    
#     # filtered_df = df[df['sentiment'].isin(sentiment_filter)]
    
#     # for idx, row in filtered_df.head(10).iterrows():
#     #     sentiment_icon = {'Positive': '🟢', 'Neutral': '⚪', 'Negative': '🔴'}.get(row['sentiment'], '⚪')
#     #     st.markdown(f"""
#     #     <div style="background: #f8f9fa; padding: 1rem; border-radius: 10px; margin-bottom: 1rem;">
#     #         <div style="display: flex; justify-content: space-between;">
#     #             <div>
#     #                 <span style="font-size: 1.2rem;">{sentiment_icon}</span>
#     #                 <strong>{row['sentiment']}</strong>
#     #                 {' 😏' if row.get('sarcasm_detected', False) else ''}
#     #             </div>
#     #             <small>{row.get('date', 'Date not available')}</small>
#     #         </div>
#     #         <p style="margin-top: 0.5rem;">{row.get('full_text', row.get('content', 'No content'))[:300]}...</p>
#     #     </div>
#     #     """, unsafe_allow_html=True)

#         # ==================== SECTION 6: SAMPLE REVIEWS ====================
#     st.markdown("---")
#     st.markdown("## 📝 Recent Customer Reviews")
    
#     # Filter options in a more compact layout
#     col1, col2, col3 = st.columns([2, 2, 1])
#     with col1:
#         sentiment_filter = st.multiselect(
#             "Filter by Sentiment",
#             options=['Positive', 'Neutral', 'Negative'],
#             default=['Positive', 'Neutral', 'Negative'],
#             key="sentiment_filter"
#         )
    
#     with col2:
#         search_term = st.text_input("🔍 Search Reviews", placeholder="Enter keyword...", key="search_reviews")
    
#     # Apply filters
#     filtered_df = df[df['sentiment'].isin(sentiment_filter)]
#     if search_term:
#         filtered_df = filtered_df[filtered_df['full_text'].str.contains(search_term, case=False, na=False)]
    
#     # Professional review cards without tags
#     for idx, row in filtered_df.head(10).iterrows():
#         # Determine sentiment icon and color
#         if row['sentiment'] == 'Positive':
#             sentiment_color = "#00ff88"
#             sentiment_icon = "✓"
#         elif row['sentiment'] == 'Negative':
#             sentiment_color = "#ff4757"
#             sentiment_icon = "✗"
#         else:
#             sentiment_color = "#ffb347"
#             sentiment_icon = "●"
        
#         # Clean review display without extra tags
#         st.markdown(f"""
#         <div style="background: #ffffff; padding: 1.2rem; border-radius: 8px; margin-bottom: 1rem; box-shadow: 0 1px 3px rgba(0,0,0,0.1); border-left: 4px solid {sentiment_color};">
#             <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
#                 <div style="display: flex; align-items: center; gap: 0.5rem;">
#                     <span style="font-size: 1.1rem; font-weight: 600; color: {sentiment_color};">{sentiment_icon}</span>
#                     <span style="font-weight: 500; color: #333;">{row['sentiment']}</span>
#                     <span style="color: #999; font-size: 0.85rem;">•</span>
#                     <span style="color: #666; font-size: 0.85rem;">Rating: {row.get('rating', 'N/A')}★</span>
#                 </div>
#                 <small style="color: #999;">{row.get('date', 'Date not available')}</small>
#             </div>
#             <p style="margin: 0.5rem 0 0 0; color: #444; line-height: 1.5;">{row.get('full_text', row.get('content', 'No content'))[:350]}{'...' if len(row.get('full_text', row.get('content', ''))) > 350 else ''}</p>
#         </div>
#         """, unsafe_allow_html=True)
    
#     # Show message if no reviews match filters
#     if len(filtered_df.head(10)) == 0:
#         st.info("No reviews match your current filters. Try adjusting the sentiment filter or search term.")
    
#     # Show count of displayed reviews
#     st.caption(f"Showing {min(10, len(filtered_df))} of {len(filtered_df)} reviews matching your criteria")
    
#     # Footer
#     st.markdown("---")
#     st.markdown("""
#     <div style="text-align: center; color: #666; padding: 2rem;">
#         <p>🚀 Built with AI Technology | Sentiment Analysis | Sarcasm Detection | Automated Reporting</p>
#         <p><small>Note: This demonstration uses pre-analyzed review data. In production, it would scrape live reviews from Trustpilot.</small></p>
#     </div>
#     """, unsafe_allow_html=True)
    
#     # New analysis button
#     col1, col2, col3 = st.columns([1, 2, 1])
#     with col2:
#         if st.button("🔄 Analyze Another Business", use_container_width=True):
#             st.session_state.app_stage = 'setup'
#             st.session_state.pop('overall_summary', None)
#             st.rerun()

# def main():
#     # Check authentication
#     if not st.session_state.authenticated:
#         login_screen()
#     else:
#         # Show main app
#         if st.session_state.app_stage == 'setup':
#             setup_screen()
#         elif st.session_state.app_stage == 'results':
#             results_screen()

# if __name__ == "__main__":
#     main()

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
from auth import AuthSystem, init_session_state, login_screen, logout

# ─────────────────────────────────────────────
# PAGE CONFIGURATION
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="Reputation Intelligence",
    page_icon="◆",
    layout="wide",
    initial_sidebar_state="collapsed"
)

init_session_state()

if 'app_stage' not in st.session_state:
    st.session_state.app_stage = 'setup'
if 'analysis_complete' not in st.session_state:
    st.session_state.analysis_complete = False
if 'report_scheduled' not in st.session_state:
    st.session_state.report_scheduled = False

# ─────────────────────────────────────────────
# GLOBAL CSS — LUXURY DARK THEME
# ─────────────────────────────────────────────
LUXURY_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@300;400;500;600;700&family=Sora:wght@200;300;400;500;600&display=swap');

/* ── Root Variables ── */
:root {
    --bg-base:       #07080c;
    --bg-surface:    #0d0f16;
    --bg-elevated:   #13161f;
    --bg-hover:      #1a1d28;
    --border:        rgba(255,255,255,0.06);
    --border-accent: rgba(196,163,90,0.35);
    --gold:          #c4a35a;
    --gold-light:    #e0c07a;
    --gold-dim:      rgba(196,163,90,0.15);
    --text-primary:  #f0ece3;
    --text-secondary:#9a9690;
    --text-muted:    #5a5750;
    --red:           #c45a5a;
    --green:         #5ac47a;
    --amber:         #c4905a;
    --font-display:  'Cormorant Garamond', Georgia, serif;
    --font-body:     'Sora', -apple-system, sans-serif;
    --radius:        4px;
    --radius-lg:     8px;
}

/* ── Global Reset ── */
html, body, [class*="css"] {
    font-family: var(--font-body) !important;
    background-color: var(--bg-base) !important;
    color: var(--text-primary) !important;
}

/* ── App Container ── */
.stApp {
    background-color: var(--bg-base) !important;
    background-image:
        radial-gradient(ellipse 80% 50% at 50% -20%, rgba(196,163,90,0.04) 0%, transparent 60%),
        radial-gradient(ellipse 40% 30% at 90% 80%, rgba(196,163,90,0.025) 0%, transparent 50%);
}

/* ── Remove Streamlit chrome ── */
#MainMenu, footer, header { visibility: hidden; }
.block-container {
    padding: 2.5rem 3.5rem 4rem !important;
    max-width: 1440px !important;
}

/* ── Typography ── */
h1, h2, h3 {
    font-family: var(--font-display) !important;
    font-weight: 400 !important;
    letter-spacing: 0.02em !important;
    color: var(--text-primary) !important;
}

p, div, span, label {
    font-family: var(--font-body) !important;
    color: var(--text-secondary) !important;
    font-size: 0.875rem !important;
    font-weight: 300 !important;
}

/* ── Metrics ── */
[data-testid="stMetric"] {
    background: var(--bg-elevated) !important;
    border: 1px solid var(--border) !important;
    border-top: 1px solid var(--border-accent) !important;
    border-radius: var(--radius) !important;
    padding: 1.5rem 1.75rem !important;
    transition: border-color 0.25s ease !important;
}
[data-testid="stMetric"]:hover {
    border-color: rgba(196,163,90,0.25) !important;
    border-top-color: var(--gold) !important;
}
[data-testid="stMetricLabel"] {
    font-family: var(--font-body) !important;
    font-size: 0.7rem !important;
    font-weight: 500 !important;
    letter-spacing: 0.12em !important;
    text-transform: uppercase !important;
    color: var(--text-muted) !important;
}
[data-testid="stMetricValue"] {
    font-family: var(--font-display) !important;
    font-size: 2.4rem !important;
    font-weight: 400 !important;
    color: var(--text-primary) !important;
    line-height: 1.1 !important;
}
[data-testid="stMetricDelta"] {
    font-size: 0.75rem !important;
    font-weight: 300 !important;
    font-family: var(--font-body) !important;
}

/* ── Buttons ── */
.stButton > button {
    background: transparent !important;
    border: 1px solid var(--border-accent) !important;
    color: var(--gold) !important;
    font-family: var(--font-body) !important;
    font-size: 0.72rem !important;
    font-weight: 500 !important;
    letter-spacing: 0.1em !important;
    text-transform: uppercase !important;
    border-radius: var(--radius) !important;
    padding: 0.65rem 1.5rem !important;
    transition: all 0.2s ease !important;
}
.stButton > button:hover {
    background: var(--gold-dim) !important;
    border-color: var(--gold) !important;
    color: var(--gold-light) !important;
    transform: translateY(-1px) !important;
    box-shadow: 0 4px 24px rgba(196,163,90,0.12) !important;
}
.stButton > button[kind="primary"] {
    background: var(--gold-dim) !important;
    border-color: var(--gold) !important;
    color: var(--gold-light) !important;
}
.stButton > button[kind="primary"]:hover {
    background: rgba(196,163,90,0.25) !important;
    box-shadow: 0 4px 32px rgba(196,163,90,0.2) !important;
}

/* ── Form Submit Button ── */
.stFormSubmitButton > button {
    background: var(--gold-dim) !important;
    border: 1px solid var(--gold) !important;
    color: var(--gold-light) !important;
    font-family: var(--font-body) !important;
    font-size: 0.72rem !important;
    font-weight: 500 !important;
    letter-spacing: 0.15em !important;
    text-transform: uppercase !important;
    border-radius: var(--radius) !important;
    padding: 0.75rem 2rem !important;
    transition: all 0.25s ease !important;
    width: 100% !important;
}
.stFormSubmitButton > button:hover {
    background: rgba(196,163,90,0.28) !important;
    box-shadow: 0 0 40px rgba(196,163,90,0.18) !important;
    transform: translateY(-1px) !important;
}

/* ── Inputs ── */
.stTextInput > div > div > input,
.stTextArea > div > div > textarea,
.stNumberInput > div > div > input {
    background: var(--bg-elevated) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius) !important;
    color: var(--text-primary) !important;
    font-family: var(--font-body) !important;
    font-size: 0.875rem !important;
    font-weight: 300 !important;
    padding: 0.7rem 1rem !important;
    transition: border-color 0.2s ease !important;
}
.stTextInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus {
    border-color: var(--gold) !important;
    box-shadow: 0 0 0 1px rgba(196,163,90,0.2) !important;
    outline: none !important;
}
.stTextInput > label,
.stTextArea > label,
.stNumberInput > label {
    font-size: 0.68rem !important;
    font-weight: 500 !important;
    letter-spacing: 0.1em !important;
    text-transform: uppercase !important;
    color: var(--text-muted) !important;
    margin-bottom: 0.4rem !important;
}

/* ── Multiselect ── */
.stMultiSelect > label {
    font-size: 0.68rem !important;
    font-weight: 500 !important;
    letter-spacing: 0.1em !important;
    text-transform: uppercase !important;
    color: var(--text-muted) !important;
}
.stMultiSelect [data-baseweb="select"] > div {
    background: var(--bg-elevated) !important;
    border-color: var(--border) !important;
    border-radius: var(--radius) !important;
}
[data-baseweb="tag"] {
    background: var(--gold-dim) !important;
    border-color: var(--border-accent) !important;
}
[data-baseweb="tag"] span { color: var(--gold) !important; }

/* ── Info / Alert boxes ── */
.stInfo {
    background: var(--bg-elevated) !important;
    border: 1px solid var(--border-accent) !important;
    border-radius: var(--radius) !important;
    color: var(--text-secondary) !important;
    font-size: 0.85rem !important;
}
.stAlert { border-radius: var(--radius) !important; }

/* ── Spinner ── */
.stSpinner > div { border-top-color: var(--gold) !important; }

/* ── Success / Error ── */
[data-baseweb="notification"] {
    background: var(--bg-elevated) !important;
    border-radius: var(--radius) !important;
}

/* ── Horizontal Rule ── */
hr {
    border: none !important;
    border-top: 1px solid var(--border) !important;
    margin: 2.5rem 0 !important;
}

/* ── Plotly Chart Backgrounds ── */
.js-plotly-plot { background: transparent !important; }

/* ── Caption ── */
.stCaption, [data-testid="stCaptionContainer"] {
    color: var(--text-muted) !important;
    font-size: 0.72rem !important;
    letter-spacing: 0.04em !important;
    font-weight: 300 !important;
}

/* ── Form ── */
[data-testid="stForm"] {
    background: transparent !important;
    border: none !important;
}

/* ── Column gaps ── */
[data-testid="column"] { gap: 1.5rem !important; }

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 4px; height: 4px; }
::-webkit-scrollbar-track { background: var(--bg-base); }
::-webkit-scrollbar-thumb { background: var(--border); border-radius: 2px; }
::-webkit-scrollbar-thumb:hover { background: var(--gold-dim); }
</style>
"""


# ─────────────────────────────────────────────
# HELPER: SECTION HEADER
# ─────────────────────────────────────────────
def section_header(title, subtitle=""):
    sub_html = f'<p style="margin:0.35rem 0 0 0; font-size:0.8rem; color:#5a5750; font-family:\'Sora\',sans-serif; font-weight:300; letter-spacing:0.04em;">{subtitle}</p>' if subtitle else ""
    return f"""
    <div style="margin:0 0 1.75rem 0; padding-bottom:1.25rem; border-bottom:1px solid rgba(255,255,255,0.06);">
        <h2 style="margin:0; font-family:'Cormorant Garamond',Georgia,serif; font-size:1.65rem; font-weight:400; letter-spacing:0.03em; color:#f0ece3;">{title}</h2>
        {sub_html}
    </div>
    """


# ─────────────────────────────────────────────
# DATA LOADERS
# ─────────────────────────────────────────────
@st.cache_data
def load_static_reviews():
    try:
        return pd.read_csv('analyzed_reviews_optimized.csv')
    except:
        try:
            return pd.read_csv('reviews.csv')
        except:
            return None

@st.cache_data
def load_insights():
    try:
        with open('insights.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return None


# ─────────────────────────────────────────────
# AI SUMMARY GENERATOR
# ─────────────────────────────────────────────
def generate_overall_summary(df, insights, business_context=""):
    total = len(df)
    positive = len(df[df['sentiment'] == 'Positive'])
    negative = len(df[df['sentiment'] == 'Negative'])
    neutral  = len(df[df['sentiment'] == 'Neutral'])

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
        return json.loads(response['message']['content'])
    except:
        return {
            "what_people_appreciate": ["Product quality", "Customer service response"],
            "what_people_dislike": ["Technical issues", "Support delays"],
            "overall_recommendation": "Focus on addressing key customer complaints to improve retention.",
            "business_health_score": 65
        }


# ─────────────────────────────────────────────
# CHARTS
# ─────────────────────────────────────────────
CHART_LAYOUT = dict(
    paper_bgcolor='rgba(0,0,0,0)',
    plot_bgcolor='rgba(0,0,0,0)',
    font=dict(family='Sora, sans-serif', color='#9a9690', size=11),
    margin=dict(l=8, r=8, t=40, b=8),
)

def create_sentiment_gauge(positive_pct):
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=positive_pct,
        number={'suffix': '%', 'font': {'family': 'Cormorant Garamond', 'size': 48, 'color': '#f0ece3'}},
        title={'text': 'SATISFACTION INDEX', 'font': {'family': 'Sora', 'size': 10, 'color': '#5a5750'}},
        gauge={
            'axis': {
                'range': [0, 100],
                'tickwidth': 0,
                'tickcolor': 'rgba(0,0,0,0)',  # Fixed: 'transparent' → 'rgba(0,0,0,0)'
                'tickfont': {'size': 9, 'color': '#5a5750'},
            },
            'bar': {'color': '#c4a35a', 'thickness': 0.18},
            'bgcolor': 'rgba(255,255,255,0.03)',
            'borderwidth': 0,
            'steps': [
                {'range': [0, 33],  'color': 'rgba(196,90,90,0.12)'},
                {'range': [33, 66], 'color': 'rgba(196,144,90,0.12)'},
                {'range': [66, 100],'color': 'rgba(90,196,122,0.12)'},
            ],
        }
    ))
    fig.update_layout(height=260, **CHART_LAYOUT)
    return fig

def create_donut_chart(df):
    counts = df['sentiment'].value_counts()
    colors = {'Positive': '#5ac47a', 'Neutral': '#c4a35a', 'Negative': '#c45a5a'}
    color_seq = [colors.get(s, '#9a9690') for s in counts.index]

    fig = go.Figure(go.Pie(
        labels=counts.index,
        values=counts.values,
        hole=0.72,
        marker=dict(colors=color_seq, line=dict(color='#07080c', width=3)),
        textinfo='label+percent',
        textfont=dict(family='Sora', size=10, color='#9a9690'),
        hovertemplate='<b>%{label}</b><br>%{value} reviews<br>%{percent}<extra></extra>',
    ))
    fig.add_annotation(
        text=f"<b>{len(df)}</b>",
        x=0.5, y=0.55, font=dict(family='Cormorant Garamond', size=36, color='#f0ece3'),
        showarrow=False
    )
    fig.add_annotation(
        text="TOTAL",
        x=0.5, y=0.38, font=dict(family='Sora', size=9, color='#5a5750'),
        showarrow=False
    )
    fig.update_layout(
        title=dict(text='SENTIMENT DISTRIBUTION', font=dict(family='Sora', size=10, color='#5a5750'), x=0.5, xanchor='center'),
        showlegend=False,
        height=320,
        **CHART_LAYOUT,
    )
    return fig

def create_sarcasm_bar(pct):
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=pct,
        number={'suffix': '%', 'font': {'family': 'Cormorant Garamond', 'size': 48, 'color': '#f0ece3'}},
        title={'text': 'SARCASM DETECTION RATE', 'font': {'family': 'Sora', 'size': 10, 'color': '#5a5750'}},
        gauge={
            'axis': {
                'range': [0, 100], 
                'tickwidth': 0, 
                'tickcolor': 'rgba(0,0,0,0)',  # Fixed: 'transparent' → 'rgba(0,0,0,0)'
                'tickfont': {'size': 9, 'color': '#5a5750'}
            },
            'bar': {'color': '#c4905a', 'thickness': 0.18},
            'bgcolor': 'rgba(255,255,255,0.03)',
            'borderwidth': 0,
            'steps': [
                {'range': [0, 100], 'color': 'rgba(196,144,90,0.08)'},
            ],
        }
    ))
    fig.update_layout(height=260, **CHART_LAYOUT)
    return fig


# ─────────────────────────────────────────────
# SETUP SCREEN
# ─────────────────────────────────────────────
def setup_screen():
    st.markdown(LUXURY_CSS, unsafe_allow_html=True)

    # Top bar
    user = st.session_state.get('user', {})
    if user:
        col_u1, col_u2 = st.columns([8, 1])
        with col_u2:
            if st.button("Sign Out", key="setup_logout_button"):
                logout()
        with col_u1:
            st.markdown(f"""
            <p style="text-align:right; font-size:0.72rem; letter-spacing:0.08em; color:#5a5750;
                       padding-top:0.4rem; text-transform:uppercase; font-family:'Sora',sans-serif;">
                {user.get('full_name', '')} &nbsp;&middot;&nbsp; {user.get('email', '')}
            </p>
            """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Hero wordmark ──
    st.markdown("""
    <div style="margin-bottom:3.5rem;">
        <p style="font-family:'Sora',sans-serif; font-size:0.68rem; letter-spacing:0.22em;
                   text-transform:uppercase; color:#c4a35a; margin:0 0 0.75rem 0; font-weight:500;">
            Reputation Intelligence Platform
        </p>
        <h1 style="font-family:'Cormorant Garamond',Georgia,serif; font-size:3.6rem;
                    font-weight:300; letter-spacing:0.04em; color:#f0ece3; margin:0; line-height:1.1;">
            Understand What Your<br>Customers Are Saying
        </h1>
        <div style="width:48px; height:1px; background:#c4a35a; margin:1.5rem 0;"></div>
        <p style="font-family:'Sora',sans-serif; font-size:0.85rem; color:#5a5750;
                   font-weight:300; max-width:480px; line-height:1.7;">
            AI-powered sentiment analysis and reputation intelligence, distilled into clear, 
            actionable insights for serious businesses.
        </p>
    </div>
    """, unsafe_allow_html=True)

    col_form, col_gap, col_info = st.columns([5, 1, 4])

    with col_form:
        st.markdown("""
        <p style="font-family:'Sora',sans-serif; font-size:0.68rem; letter-spacing:0.14em;
                   text-transform:uppercase; color:#5a5750; margin-bottom:1.5rem; font-weight:500;">
            Analysis Configuration
        </p>
        """, unsafe_allow_html=True)

        with st.form(key="business_setup_form"):
            trustpilot_url = st.text_input(
                "Trustpilot Business URL",
                placeholder="https://www.trustpilot.com/review/company.com",
                help="Enter the Trustpilot URL for the business you want to analyse",
                key="setup_url_input"
            )

            default_email = user.get('email', '') if user else ""
            email = st.text_input(
                "Email Address",
                placeholder="name@company.com",
                value=default_email,
                disabled=bool(user),
                key="setup_email_input"
            )

            default_business = user.get('business_name', '') if user else ""
            business_name = st.text_input(
                "Business Name",
                placeholder="Acme Corporation",
                value=default_business,
                key="setup_business_name_input"
            )

            business_context = st.text_area(
                "Business Context  (optional)",
                placeholder="Describe your business, products, or areas of concern...",
                height=96,
                key="setup_context_input"
            )

            st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)
            submitted = st.form_submit_button("Run Analysis", type="primary", use_container_width=True)

            if submitted:
                if not email:
                    st.error("An email address is required.")
                else:
                    st.session_state.business_info = {
                        'url':              trustpilot_url or "demo.trustpilot.com/review/company",
                        'email':            email,
                        'business_name':    business_name or user.get('business_name', 'Business'),
                        'business_context': business_context,
                        'analysis_time':    datetime.now()
                    }
                    st.session_state.app_stage = 'results'
                    st.rerun()

    with col_info:
        st.markdown("<br><br>", unsafe_allow_html=True)
        capabilities = [
            ("Sentiment Analysis",   "Classify every review as positive, negative, or neutral with nuanced context awareness."),
            ("Sarcasm Detection",    "Identify hidden negativity masked by superficially positive language."),
            ("Prioritised Problems", "Surface the highest-impact issues ranked by frequency and severity."),
            ("Automated Reporting",  "Schedule recurring intelligence reports delivered directly to your inbox."),
        ]
        for title, desc in capabilities:
            st.markdown(f"""
            <div style="margin-bottom:1.5rem; padding:1.25rem 1.5rem;
                        background:#0d0f16; border:1px solid rgba(255,255,255,0.05);
                        border-left:2px solid #c4a35a; border-radius:4px;">
                <p style="font-family:'Sora',sans-serif; font-size:0.72rem; font-weight:500;
                           letter-spacing:0.08em; text-transform:uppercase;
                           color:#c4a35a; margin:0 0 0.4rem 0;">{title}</p>
                <p style="font-family:'Sora',sans-serif; font-size:0.8rem; font-weight:300;
                           color:#5a5750; line-height:1.65; margin:0;">{desc}</p>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("""
        <p style="font-family:'Sora',sans-serif; font-size:0.68rem; letter-spacing:0.04em;
                   color:#3a3730; margin-top:1rem; line-height:1.6;">
            This demonstration operates on pre-analysed review data.<br>
            Production deployments support live Trustpilot ingestion.
        </p>
        """, unsafe_allow_html=True)


# ─────────────────────────────────────────────
# RESULTS SCREEN
# ─────────────────────────────────────────────
def results_screen():
    st.markdown(LUXURY_CSS, unsafe_allow_html=True)

    # Top navigation bar
    col_nav1, col_nav2, col_nav3 = st.columns([6, 2, 1])
    with col_nav1:
        st.markdown("""
        <p style="font-family:'Cormorant Garamond',Georgia,serif; font-size:1.05rem;
                   letter-spacing:0.08em; color:#c4a35a; padding-top:0.25rem;">
            REPUTATION INTELLIGENCE
        </p>
        """, unsafe_allow_html=True)
    with col_nav3:
        if st.button("Sign Out", key="results_logout_button"):
            logout()

    st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)

    # Load data
    df       = load_static_reviews()
    insights = load_insights()

    if df is None:
        st.error("Review data not found. Ensure 'analyzed_reviews_optimized.csv' is present.")
        if st.button("Back to Setup"):
            st.session_state.app_stage = 'setup'
            st.rerun()
        return

    # Compute metrics
    total_reviews     = len(df)
    negative_count    = len(df[df['sentiment'] == 'Negative'])
    positive_count    = len(df[df['sentiment'] == 'Positive'])
    neutral_count     = len(df[df['sentiment'] == 'Neutral'])
    negative_pct      = (negative_count / total_reviews) * 100
    positive_pct      = (positive_count / total_reviews) * 100

    # Generate AI summary
    if 'overall_summary' not in st.session_state:
        with st.spinner("Generating intelligence report..."):
            st.session_state.overall_summary = generate_overall_summary(
                df, insights, st.session_state.business_info.get('business_context', '')
            )

    business_name = st.session_state.business_info.get('business_name', 'Business')
    summary       = st.session_state.overall_summary

    # ── Page heading ──
    st.markdown(f"""
    <div style="margin-bottom:2.5rem;">
        <p style="font-family:'Sora',sans-serif; font-size:0.65rem; letter-spacing:0.2em;
                   text-transform:uppercase; color:#5a5750; margin:0 0 0.5rem 0;">
            Reputation Report &nbsp;&middot;&nbsp; {datetime.now().strftime('%d %B %Y')}
        </p>
        <h1 style="font-family:'Cormorant Garamond',Georgia,serif; font-size:2.8rem;
                    font-weight:400; letter-spacing:0.03em; color:#f0ece3; margin:0; line-height:1.15;">
            {business_name}
        </h1>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # ══════════════════════════════════
    # SECTION 1 — KEY METRICS
    # ══════════════════════════════════
    st.markdown(section_header("Performance Metrics", "Aggregated sentiment across all captured reviews"), unsafe_allow_html=True)

    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.metric("Total Reviews",    f"{total_reviews:,}")
    with m2:
        st.metric("Negative Reviews", f"{negative_count:,}", delta=f"{negative_pct:.1f}% of total")
    with m3:
        st.metric("Positive Reviews", f"{positive_count:,}", delta=f"{positive_pct:.1f}% of total")
    with m4:
        st.metric("Neutral Reviews",  f"{neutral_count:,}")

    st.markdown("---")

    # ══════════════════════════════════
    # SECTION 2 — PROBLEMS & SOLUTIONS
    # ══════════════════════════════════
    st.markdown(section_header("Identified Issues & Recommended Actions", "Ranked by frequency and customer impact"), unsafe_allow_html=True)

    if insights and 'problems' in insights:
        problems    = insights['problems']
        suggestions = insights['suggestions']
        severities  = insights.get('severity', ['Medium'] * len(problems))
        cols        = st.columns(len(problems))

        sev_palette = {
            'High':   ('#c45a5a', 'rgba(196,90,90,0.08)',   '01'),
            'Medium': ('#c4a35a', 'rgba(196,163,90,0.08)',  '02'),
            'Low':    ('#5ac47a', 'rgba(90,196,122,0.08)',  '03'),
        }

        for idx, (col, problem, suggestion, severity) in enumerate(zip(cols, problems, suggestions, severities)):
            accent, bg, num = sev_palette.get(severity, ('#9a9690', 'rgba(154,150,144,0.08)', '0' + str(idx+1)))
            with col:
                st.markdown(f"""
                <div style="background:{bg}; border:1px solid rgba(255,255,255,0.05);
                             border-top:2px solid {accent}; border-radius:4px;
                             padding:1.5rem 1.5rem 1.75rem; height:100%;">
                    <p style="font-family:'Sora',sans-serif; font-size:0.6rem; letter-spacing:0.18em;
                               text-transform:uppercase; color:{accent}; margin:0 0 1rem 0; font-weight:500;">
                        Issue {num} &nbsp;&middot;&nbsp; {severity} Priority
                    </p>
                    <p style="font-family:'Cormorant Garamond',Georgia,serif; font-size:1.15rem;
                               font-weight:500; color:#f0ece3; margin:0 0 1rem 0; line-height:1.45;">
                        {problem}
                    </p>
                    <div style="width:24px; height:1px; background:{accent}; margin-bottom:1rem; opacity:0.5;"></div>
                    <p style="font-family:'Sora',sans-serif; font-size:0.78rem; font-weight:300;
                               color:#6a6760; line-height:1.65; margin:0;">
                        {suggestion}
                    </p>
                </div>
                """, unsafe_allow_html=True)
    else:
        st.info("No insights data available.")

    st.markdown("---")

    # ══════════════════════════════════
    # SECTION 3 — ANALYSIS SUMMARY
    # ══════════════════════════════════
    st.markdown(section_header("AI Intelligence Summary", "Synthesised from full review corpus"), unsafe_allow_html=True)

    col_app, col_gap2, col_dis = st.columns([5, 1, 5])
    with col_app:
        st.markdown("""
        <p style="font-family:'Sora',sans-serif; font-size:0.65rem; letter-spacing:0.14em;
                   text-transform:uppercase; color:#5ac47a; margin-bottom:1rem; font-weight:500;">
            Customer Appreciation
        </p>
        """, unsafe_allow_html=True)
        for point in summary.get('what_people_appreciate', []):
            st.markdown(f"""
            <div style="display:flex; align-items:flex-start; gap:0.75rem; margin-bottom:0.75rem;">
                <div style="width:4px; height:4px; background:#5ac47a; border-radius:50%;
                             margin-top:0.45rem; flex-shrink:0;"></div>
                <p style="font-family:'Sora',sans-serif; font-size:0.83rem; font-weight:300;
                           color:#9a9690; line-height:1.6; margin:0;">{point}</p>
            </div>
            """, unsafe_allow_html=True)

    with col_dis:
        st.markdown("""
        <p style="font-family:'Sora',sans-serif; font-size:0.65rem; letter-spacing:0.14em;
                   text-transform:uppercase; color:#c45a5a; margin-bottom:1rem; font-weight:500;">
            Areas of Concern
        </p>
        """, unsafe_allow_html=True)
        for point in summary.get('what_people_dislike', []):
            st.markdown(f"""
            <div style="display:flex; align-items:flex-start; gap:0.75rem; margin-bottom:0.75rem;">
                <div style="width:4px; height:4px; background:#c45a5a; border-radius:50%;
                             margin-top:0.45rem; flex-shrink:0;"></div>
                <p style="font-family:'Sora',sans-serif; font-size:0.83rem; font-weight:300;
                           color:#9a9690; line-height:1.6; margin:0;">{point}</p>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)
    st.markdown(f"""
    <div style="background:#0d0f16; border:1px solid rgba(196,163,90,0.15);
                border-left:2px solid #c4a35a; border-radius:4px; padding:1.5rem 1.75rem;">
        <p style="font-family:'Sora',sans-serif; font-size:0.65rem; letter-spacing:0.14em;
                   text-transform:uppercase; color:#c4a35a; margin:0 0 0.65rem 0; font-weight:500;">
            Strategic Recommendation
        </p>
        <p style="font-family:'Sora',sans-serif; font-size:0.85rem; font-weight:300;
                   color:#9a9690; line-height:1.75; margin:0;">
            {summary.get('overall_recommendation', 'Focus on addressing core customer feedback.')}
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # ══════════════════════════════════
    # SECTION 4 — VISUALISATIONS
    # ══════════════════════════════════
    st.markdown(section_header("Analytics", "Visual breakdown of sentiment patterns"), unsafe_allow_html=True)

    v1, v2, v3 = st.columns([4, 4, 4])
    with v1:
        st.plotly_chart(create_donut_chart(df), use_container_width=True)
    with v2:
        st.plotly_chart(create_sentiment_gauge(positive_pct), use_container_width=True)
        health = summary.get('business_health_score', 65)
        st.markdown(f"""
        <p style="text-align:center; font-family:'Sora',sans-serif; font-size:0.65rem;
                   letter-spacing:0.1em; text-transform:uppercase; color:#5a5750; margin-top:-0.5rem;">
            Health Score &nbsp;—&nbsp; {health} / 100
        </p>
        """, unsafe_allow_html=True)
    with v3:
        if 'sarcasm_detected' in df.columns:
            sarcasm_pct = (df['sarcasm_detected'].sum() / total_reviews) * 100
            st.plotly_chart(create_sarcasm_bar(sarcasm_pct), use_container_width=True)
        else:
            # Sentiment bar chart as fallback
            sent_data = df['sentiment'].value_counts().reset_index()
            sent_data.columns = ['Sentiment', 'Count']
            color_map = {'Positive': '#5ac47a', 'Neutral': '#c4a35a', 'Negative': '#c45a5a'}
            fig_bar = go.Figure(go.Bar(
                x=sent_data['Sentiment'],
                y=sent_data['Count'],
                marker_color=[color_map.get(s, '#9a9690') for s in sent_data['Sentiment']],
                marker_line_width=0,
            ))
            fig_bar.update_layout(
                title=dict(text='REVIEW VOLUME', font=dict(family='Sora', size=10, color='#5a5750'), x=0.5, xanchor='center'),
                xaxis=dict(showgrid=False, tickfont=dict(size=9)),
                yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.04)', tickfont=dict(size=9)),
                height=320,
                **CHART_LAYOUT,
            )
            st.plotly_chart(fig_bar, use_container_width=True)

    st.markdown("---")

    # ══════════════════════════════════
    # SECTION 5 — REPORT DELIVERY
    # ══════════════════════════════════
    st.markdown(section_header("Report Delivery", "Configure automated intelligence distribution"), unsafe_allow_html=True)

    _, col_rep, _ = st.columns([3, 4, 3])
    with col_rep:
        report_email  = st.text_input(
            "Recipient Email",
            value=st.session_state.business_info.get('email', ''),
            key="report_email"
        )
        interval_days = st.number_input(
            "Report Frequency (Days)",
            min_value=1, max_value=30, value=7
        )

        st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)

        btn1, btn2 = st.columns(2)
        with btn1:
            if st.button("Send Report Now", type="primary", use_container_width=True):
                if report_email:
                    with st.spinner("Compiling and transmitting report..."):
                        try:
                            reporter = EmailReporter()
                            success  = reporter.send_report_email(report_email, "ondemand", include_pdf=True)
                            if success:
                                st.success(f"Report dispatched to {report_email}")
                                st.info("Review delivery at http://localhost:8025")
                            else:
                                st.error("Delivery failed. Verify MailHog is running.")
                        except Exception as e:
                            st.error(f"Error: {e}")
                else:
                    st.warning("Enter a recipient email address.")

        with btn2:
            if st.button("Schedule Reports", use_container_width=True):
                if report_email:
                    next_dt = (datetime.now() + timedelta(days=interval_days)).strftime('%d %B %Y')
                    st.success(f"Scheduled every {interval_days} day(s)")
                    st.info(f"Next delivery: {next_dt}")
                    st.session_state.report_scheduled = True
                else:
                    st.warning("Enter a recipient email address.")

    st.markdown("---")

    # ══════════════════════════════════
    # SECTION 6 — REVIEW EXPLORER
    # ══════════════════════════════════
    st.markdown(section_header("Review Explorer", "Browse and search individual customer reviews"), unsafe_allow_html=True)

    fc1, fc2 = st.columns([3, 5])
    with fc1:
        sentiment_filter = st.multiselect(
            "Filter by Sentiment",
            options=['Positive', 'Neutral', 'Negative'],
            default=['Positive', 'Neutral', 'Negative'],
            key="sentiment_filter"
        )
    with fc2:
        search_term = st.text_input("Search Reviews", placeholder="Enter keyword...", key="search_reviews")

    filtered_df = df[df['sentiment'].isin(sentiment_filter)]
    if search_term:
        filtered_df = filtered_df[filtered_df['full_text'].str.contains(search_term, case=False, na=False)]

    st.markdown("<div style='height:0.75rem'></div>", unsafe_allow_html=True)

    snt_cfg = {
        'Positive': ('#5ac47a', 'Positive'),
        'Negative': ('#c45a5a', 'Negative'),
        'Neutral':  ('#c4a35a', 'Neutral'),
    }

    for _, row in filtered_df.head(10).iterrows():
        snt        = row['sentiment']
        color, lbl = snt_cfg.get(snt, ('#9a9690', snt))
        date_str   = row.get('date', '')
        rating     = row.get('rating', '')
        text       = str(row.get('full_text', row.get('content', '')))
        preview    = text[:320] + ('...' if len(text) > 320 else '')

        rating_html = f'<span style="color:#5a5750;">&nbsp;&middot;&nbsp; {rating} / 5</span>' if rating != '' else ''

        st.markdown(f"""
        <div style="background:#0d0f16; border:1px solid rgba(255,255,255,0.05);
                     border-left:2px solid {color}; border-radius:4px;
                     padding:1.25rem 1.5rem; margin-bottom:0.85rem;
                     transition:border-color 0.2s;">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:0.65rem;">
                <span style="font-family:'Sora',sans-serif; font-size:0.65rem; letter-spacing:0.12em;
                              text-transform:uppercase; color:{color}; font-weight:500;">
                    {lbl}{rating_html}
                </span>
                <span style="font-family:'Sora',sans-serif; font-size:0.7rem; color:#3a3730; font-weight:300;">
                    {date_str}
                </span>
            </div>
            <p style="font-family:'Sora',sans-serif; font-size:0.82rem; font-weight:300;
                       color:#6a6760; line-height:1.7; margin:0;">
                {preview}
            </p>
        </div>
        """, unsafe_allow_html=True)

    if filtered_df.head(10).empty:
        st.info("No reviews match your current filters.")

    st.markdown(f"""
    <p style="font-family:'Sora',sans-serif; font-size:0.68rem; letter-spacing:0.06em;
               color:#3a3730; margin-top:0.5rem;">
        Displaying {min(10, len(filtered_df))} of {len(filtered_df)} matching reviews
    </p>
    """, unsafe_allow_html=True)

    # Footer
    st.markdown("---")
    col_f1, col_f2, col_f3 = st.columns([3, 2, 3])
    with col_f2:
        if st.button("Run New Analysis", use_container_width=True):
            st.session_state.app_stage = 'setup'
            st.session_state.pop('overall_summary', None)
            st.rerun()

    st.markdown("""
    <div style="text-align:center; padding:2.5rem 0 1rem;">
        <p style="font-family:'Sora',sans-serif; font-size:0.65rem; letter-spacing:0.12em;
                   text-transform:uppercase; color:#2a2820;">
            Reputation Intelligence Platform &nbsp;&middot;&nbsp; Powered by AI
        </p>
    </div>
    """, unsafe_allow_html=True)


# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────
def main():
    if not st.session_state.authenticated:
        # Inject luxury CSS on login screen too
        st.markdown(LUXURY_CSS, unsafe_allow_html=True)
        login_screen()
    else:
        if st.session_state.app_stage == 'setup':
            setup_screen()
        elif st.session_state.app_stage == 'results':
            results_screen()

if __name__ == "__main__":
    main()