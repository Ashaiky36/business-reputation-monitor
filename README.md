# Business Reputation Monitoring System

An intelligent, end-to-end reputation management tool that helps businesses monitor, analyze, and respond to customer reviews using advanced AI.

## 🚀 Features

- **Smart Review Scraping** - Automatically collects reviews from Trustpilot
- **Advanced Sentiment Analysis** - Detects not just positive/negative but also sarcasm using hybrid LLM approach
- **AI-Powered Insights** - Generates actionable problem summaries and solutions from negative reviews
- **Interactive Dashboard** - Modern, real-time visualization of reputation metrics
- **Automated Reporting** - Scheduled daily/weekly PDF reports delivered to email
- **Local Processing** - All data stays on your machine using local LLMs (Ollama)

## 🛠️ Tech Stack

- **Frontend**: Streamlit, Plotly
- **Backend**: Python, Pandas
- **AI/ML**: Hugging Face Transformers, Ollama (Mistral), RoBERTa
- **Reporting**: ReportLab PDF generation, MailHog (local email testing)
- **Scraping**: BeautifulSoup4, Requests

## 📦 Current Version Status

**MVP Complete** - All core features working:
- ✅ Trustpilot review scraping (30 reviews)
- ✅ Sentiment + sarcasm detection (84% accuracy, 4x speed optimized)
- ✅ AI insights generation
- ✅ Interactive dashboard with visualizations
- ✅ PDF report generation
- ✅ Automated email reporting (MailHog integration)

## 🎯 Use Case

Perfect for small business owners, marketing teams, or customer success managers who want to:
- Track online reputation without manual review reading
- Identify hidden customer frustrations (including sarcastic feedback)
- Get actionable insights rather than just sentiment scores
- Receive automated reports without logging into multiple platforms

## 🔧 Local Setup

```bash
git clone [your-repo-url]
cd business-reputation-monitor
pip install -r requirements.txt
streamlit run app.py



### **GitHub Topics (tags) for discoverability:**
business-intelligence, sentiment-analysis, reputation-management, streamlit, ai, nlp, sarcasm-detection, trustpilot, customer-feedback, review-monitoring, python, pandas, plotly, ollama, transformers
