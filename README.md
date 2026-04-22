# 📊 Business Reputation Monitoring System

[![Python 3.9+](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-red.svg)](https://streamlit.io/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Ollama](https://img.shields.io/badge/Ollama-Mistral_7B-purple.svg)](https://ollama.ai/)
[![ReportLab](https://img.shields.io/badge/ReportLab-4.0+-orange.svg)](https://www.reportlab.com/)

> An AI-powered, end-to-end reputation management tool that helps businesses monitor, analyze, and respond to customer reviews — using advanced sentiment analysis, sarcasm detection, and automated reporting. Fully local. Zero API costs.

---

## 📋 Table of Contents

- [Overview](#-overview)
- [Features](#-features)
- [Technology Stack](#️-technology-stack)
- [System Architecture](#-system-architecture)
- [Prerequisites](#-prerequisites)
- [Installation Guide](#-installation-guide)
- [Usage](#-usage)
- [Performance Metrics](#-performance-metrics)
- [Use Cases](#-use-cases)
- [Troubleshooting](#-troubleshooting)
- [Future Scope](#-future-scope)
- [Contributing](#-contributing)
- [License](#-license)

---

## 🌐 Overview

The **Business Reputation Monitoring System** is a fully local, privacy-first application that automates the process of tracking and analyzing what customers are saying about your business online. It scrapes reviews from Trustpilot, runs them through a transformer-based sentiment model, detects sarcastic reviews using a hybrid LLM pipeline, and generates professional PDF reports — all without spending a cent on external APIs.

Built with Streamlit for an interactive web UI, it's designed to be accessible to non-technical business owners while being powerful enough for data-driven teams.

---

## 🚀 Features

### 🔐 User Authentication
- Secure signup and login system with **SHA-256 password hashing**
- Persistent user sessions backed by a lightweight **SQLite database**
- Each user account maintains its own analysis history and report schedule

### 📊 Review Scraping
- Automated collection of **up to 30 Trustpilot reviews** per analysis run
- Extracts reviewer name, star rating, review text, date, and verified status
- Resilient scraping pipeline handles pagination and anti-bot measures gracefully

### 🤖 AI Sentiment Analysis
- Powered by **CardiffNLP's Twitter RoBERTa** transformer model for nuanced sentiment classification
- Classifies reviews into **Positive**, **Neutral**, and **Negative** categories
- Provides confidence scores alongside each classification for transparency

### 😏 Sarcasm Detection
- Hybrid two-stage pipeline:
  1. **Fast pattern matcher** — rule-based filter eliminates obvious non-sarcastic reviews instantly
  2. **Ollama Mistral LLM** — deep language model verification only for ambiguous cases
- Achieves **84% accuracy** validated against a Gemini baseline
- Dramatically reduces LLM calls, cutting analysis time without sacrificing quality

### 💡 AI-Powered Insights
- Automatically identifies the **top recurring problems** from negative and neutral reviews
- Assigns **severity levels** to each issue based on frequency and sentiment intensity
- Suggests **actionable solutions** for business owners to address each problem

### 📈 Interactive Dashboard
- Real-time visualizations built with **Plotly** and **Streamlit**
- Charts include sentiment distribution, rating breakdown, sarcasm flags, trend lines, and word clouds
- Fully interactive — filter, zoom, and hover for deeper data exploration

### 📧 Automated Reporting
- Schedule **daily or weekly email reports** delivered to any inbox
- Reports include a summary, key metrics, top issues, and a full PDF attachment
- Local email testing powered by **MailHog** — no external SMTP configuration required

### 📄 PDF Generation
- Professional, multi-page PDF reports generated with **ReportLab**
- Includes brand-friendly formatting: charts, tables, severity badges, and AI insight summaries
- Ready to share with stakeholders, investors, or your customer service team

---

## 🛠️ Technology Stack

| Category | Technology | Version | Purpose |
|---|---|---|---|
| Frontend | Streamlit | 1.28+ | Web application framework |
| Visualization | Plotly | 5.17+ | Interactive charts & graphs |
| Data Processing | Pandas | 2.0+ | CSV manipulation & tabular analysis |
| Data Processing | NumPy | Latest | Numerical computation |
| Web Scraping | BeautifulSoup4 | Latest | HTML parsing for review extraction |
| Web Scraping | Requests | Latest | HTTP requests to Trustpilot |
| Sentiment Model | CardiffNLP Twitter RoBERTa | Latest | Base sentiment classification |
| Sarcasm Detection | Custom Pattern Matcher | — | Rule-based pre-filter |
| LLM Integration | Ollama (Mistral 7B) | Latest | Sarcasm verification & AI insights |
| PDF Generation | ReportLab | 4.0+ | Professional report creation |
| Email Testing | MailHog | Latest | Local SMTP server |
| Database | SQLite3 | Built-in | User authentication & data storage |
| Security | SHA-256 Hashing | Built-in | Password encryption |

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Streamlit Frontend                      │
│         (Dashboard · Auth · Scheduler · Reports)           │
└────────────────────────┬────────────────────────────────────┘
                         │
          ┌──────────────▼──────────────┐
          │       Core Pipeline         │
          │                             │
          │  1. Trustpilot Scraper      │
          │  2. RoBERTa Sentiment Model │
          │  3. Sarcasm Detector        │
          │     ├─ Pattern Matcher      │
          │     └─ Ollama Mistral LLM  │
          │  4. AI Insights Generator   │
          │  5. PDF Report Builder      │
          └──────────────┬──────────────┘
                         │
     ┌───────────────────┼───────────────────┐
     │                   │                   │
┌────▼────┐        ┌─────▼─────┐      ┌─────▼──────┐
│ SQLite  │        │  Plotly   │      │  MailHog   │
│   DB    │        │  Charts   │      │   SMTP     │
│ (Auth)  │        │(Dashboard)│      │ (Reports)  │
└─────────┘        └───────────┘      └────────────┘
```

---

## 📋 Prerequisites

### System Requirements

| Requirement | Minimum | Recommended |
|---|---|---|
| Operating System | Windows 10, Linux, macOS | Windows 11 / Ubuntu 22.04 |
| RAM | 8 GB | 16 GB |
| Free Storage | 5 GB | 10 GB |
| Python Version | 3.9 | 3.11+ |

### Required External Software

- **[Ollama](https://ollama.ai/)** — Runs the Mistral 7B model locally for sarcasm detection and AI insights
- **MailHog** — Local SMTP server for email report testing (executable included in the project folder)

---

## 🔧 Installation Guide

### Step 1: Clone the Repository

```bash
git clone https://github.com/yourusername/business-reputation-monitor.git
cd business-reputation-monitor
```

### Step 2: Create a Virtual Environment

It is strongly recommended to use a virtual environment to avoid dependency conflicts.

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Install Python Dependencies

```bash
pip install -r requirements.txt
```

> **Note:** The first run will also download the RoBERTa model weights (~500MB). Ensure you have a stable internet connection.

### Step 4: Install Ollama and Pull the Mistral Model

1. Download and install Ollama from [https://ollama.ai](https://ollama.ai)
2. Pull the Mistral 7B model:

```bash
ollama pull mistral
```

> This will download approximately 4GB. The model runs entirely on your machine — no data is sent to any external server.

### Step 5: Start MailHog (Email Testing)

MailHog is a local email server that captures all outgoing emails for safe testing.

```bash
# Windows — double-click the executable in the project folder, or run:
.\MailHog.exe

# macOS / Linux
./MailHog
```

Once running, you can view captured emails at [http://localhost:8025](http://localhost:8025).

### Step 6: Launch the Application

```bash
streamlit run app.py
```

The app will open automatically in your browser at **[http://localhost:8501](http://localhost:8501)**.

---

## 🖥️ Usage

1. **Sign up** for an account on the authentication page
2. **Enter a Trustpilot URL** for the business you want to analyze (e.g., `https://www.trustpilot.com/review/example.com`)
3. Click **"Run Analysis"** — the pipeline will scrape reviews, classify sentiment, detect sarcasm, and generate insights
4. Explore the **interactive dashboard** to review charts, flagged reviews, and AI-generated problem summaries
5. **Download the PDF report** or configure the **email scheduler** to receive automated reports

---

## 📈 Performance Metrics

| Metric | Value | Notes |
|---|---|---|
| Review Processing Time | ~4 minutes | For 30 reviews end-to-end |
| Sarcasm Detection Accuracy | **84%** | Validated against Gemini baseline |
| Speed Improvement | **3.9×** | Optimized from ~17 mins to ~4 mins |
| LLM Calls per Analysis | 1–2 batches | Batching reduces Ollama overhead |
| Approximate Memory Usage | 2–4 GB | Varies with LLM load |
| External API Cost | **$0.00** | Fully local — no paid APIs used |

---

## 🎯 Use Cases

| Use Case | Description |
|---|---|
| **Small Business Reputation Tracking** | Affordable, automated monitoring without agency fees |
| **Customer Service Improvement** | Surface recurring complaints and route them to support teams |
| **Marketing Performance Measurement** | Track sentiment shifts after campaigns or product launches |
| **Product Development Feedback** | Extract specific feature or quality complaints from reviews |
| **Automated Stakeholder Reporting** | Scheduled executive summaries with professional PDF attachments |

---

## 🔍 Troubleshooting

| Problem | Solution |
|---|---|
| MailHog not detected | Start `MailHog.exe` and refresh the page |
| Email not sending | Ensure the MailHog terminal window is open and running |
| AI insights not generating | Ensure Ollama is running — verify with `ollama list` in your terminal |
| Port 8501 already in use | Run `streamlit run app.py --server.port 8502` |
| Virtual environment not activating (Windows) | Run `venv\Scripts\activate.bat` explicitly |
| RoBERTa model fails to load | Delete the cached model in `~/.cache/huggingface` and re-run |
| Scraping returns 0 reviews | The Trustpilot URL may be malformed — ensure it follows `trustpilot.com/review/<domain>` |

---

## 🔮 Future Scope

The following enhancements are planned for upcoming releases:

- **Multi-Platform Review Support** — Google Maps, Yelp, Justdial, and G2
- **Centralized AI Reply System** — Suggested responses for negative reviews, ready to copy-paste
- **Multi-Lingual Sentiment Analysis** — Support for reviews in non-English languages
- **Real-Time Alert System** — Instant notifications when negative sentiment spikes
- **Historical Trend Analytics** — Month-over-month sentiment comparison and charting
- **Competitor Benchmarking** — Side-by-side reputation analysis against competitors
- **Cloud Deployment** — Docker-based deployment with multi-tenant user management

---

## 🤝 Contributing

Contributions are welcome and appreciated! To contribute:

1. **Fork** the repository
2. **Create** a new feature branch (`git checkout -b feature/your-feature-name`)
3. **Commit** your changes with a clear message (`git commit -m 'Add: feature description'`)
4. **Push** to your fork (`git push origin feature/your-feature-name`)
5. **Open a Pull Request** describing what you've changed and why

Please ensure your code follows PEP 8 style guidelines and includes appropriate comments.

---

## 📄 License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.

---

<p align="center">Built with ❤️ using Python, Streamlit, and open-source AI</p>
