import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import pandas as pd
import json
from datetime import datetime
import os
import schedule
import time
import threading
from pdf_report_generator import PDFReportGenerator

# class EmailReporter:
    # def __init__(self, sender_email=None, sender_password=None, smtp_server="smtp.gmail.com", smtp_port=587):
    #     """
    #     Initialize Email Reporter
        
    #     For Gmail:
    #     1. Use App Password (recommended): https://myaccount.google.com/apppasswords
    #     2. Or use your regular password (less secure)
        
    #     For testing: Use a temporary email service or your personal email
    #     """
    #     self.sender_email = sender_email or os.getenv('SENDER_EMAIL', 'your_email@gmail.com')
    #     self.sender_password = sender_password or os.getenv('SENDER_PASSWORD', 'your_app_password')
    #     self.smtp_server = smtp_server
    #     self.smtp_port = smtp_port
    #     self.scheduled_jobs = {}
        
    # def send_report_email(self, recipient_email, report_type="weekly", include_pdf=True):
    #     """
    #     Send reputation report via email
    #     """
    #     try:
    #         # Create message
    #         msg = MIMEMultipart()
    #         msg['From'] = self.sender_email
    #         msg['To'] = recipient_email
    #         msg['Subject'] = f"Business Reputation Report - {datetime.now().strftime('%B %d, %Y')}"
            
    #         # Create email body
    #         body = self.create_email_body(report_type)
    #         msg.attach(MIMEText(body, 'html'))
            
    #         # Attach PDF report if requested
    #         if include_pdf:
    #             pdf_file = self.generate_pdf_report()
    #             if pdf_file and os.path.exists(pdf_file):
    #                 with open(pdf_file, "rb") as attachment:
    #                     part = MIMEBase('application', 'octet-stream')
    #                     part.set_payload(attachment.read())
    #                     encoders.encode_base64(part)
    #                     part.add_header(
    #                         'Content-Disposition',
    #                         f'attachment; filename= {os.path.basename(pdf_file)}'
    #                     )
    #                     msg.attach(part)
            
    #         # Send email
    #         with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
    #             server.starttls()
    #             server.login(self.sender_email, self.sender_password)
    #             server.send_message(msg)
            
    #         print(f"✅ Report sent successfully to {recipient_email}")
    #         return True
            
    #     except Exception as e:
    #         print(f"❌ Failed to send email: {e}")
    #         return False

class EmailReporter:
    def __init__(self, sender_email=None, sender_password=None, smtp_server=None, smtp_port=None):
        """
        Initialize Email Reporter - Now supports custom SMTP servers
        """
        # Allow environment variables or passed parameters
        self.sender_email = sender_email or os.getenv('SENDER_EMAIL', 'test@business-reputation.local')
        self.sender_password = sender_password or os.getenv('SENDER_PASSWORD', 'any_password')
        # Use custom SMTP settings if provided, otherwise default to localhost for testing
        self.smtp_server = smtp_server or os.getenv('SMTP_SERVER', 'localhost')
        self.smtp_port = int(smtp_port or os.getenv('SMTP_PORT', '1025'))
        
        self.scheduled_jobs = {}
        
        # No login required for local test servers, but we keep the variable for compatibility
        print(f"📧 Email Reporter initialized with SMTP: {self.smtp_server}:{self.smtp_port}")

    def send_report_email(self, recipient_email, report_type="weekly", include_pdf=True):
        """
        Send reputation report via email
        """
        try:
            # Create message
            msg = MIMEMultipart()
            msg['From'] = self.sender_email
            msg['To'] = recipient_email
            msg['Subject'] = f"Business Reputation Report - {datetime.now().strftime('%B %d, %Y')}"
            
            # Create email body
            body = self.create_email_body(report_type)
            msg.attach(MIMEText(body, 'html'))
            
            # Attach PDF report if requested
            if include_pdf:
                pdf_file = self.generate_pdf_report()
                if pdf_file and os.path.exists(pdf_file):
                    with open(pdf_file, "rb") as attachment:
                        part = MIMEBase('application', 'octet-stream')
                        part.set_payload(attachment.read())
                        encoders.encode_base64(part)
                        part.add_header(
                            'Content-Disposition',
                            f'attachment; filename= {os.path.basename(pdf_file)}'
                        )
                        msg.attach(part)
            
            # Connect to the SMTP server (no login required for local test servers)
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                # Only attempt login if credentials are provided and not using default test values
                if self.sender_email != "test@business-reputation.local" and self.sender_password != "any_password":
                    server.starttls()
                    server.login(self.sender_email, self.sender_password)
                
                server.send_message(msg)
            
            print(f"✅ Report sent successfully to {recipient_email}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to send email: {e}")
            return False    
    
    def create_email_body(self, report_type="weekly"):
        """Create HTML email body with key insights"""
        # Load latest data
        try:
            df = pd.read_csv('analyzed_reviews_optimized.csv')
            with open('insights.json', 'r', encoding='utf-8') as f:
                insights = json.load(f)
        except:
            df = None
            insights = None
        
        # Calculate metrics
        if df is not None:
            total_reviews = len(df)
            negative_count = len(df[df['sentiment'] == 'Negative'])
            positive_count = len(df[df['sentiment'] == 'Positive'])
            neutral_count = len(df[df['sentiment'] == 'Neutral'])
            sarcasm_count = df['sarcasm_detected'].sum()
            negative_percentage = (negative_count / total_reviews) * 100 if total_reviews > 0 else 0
        else:
            total_reviews = negative_count = positive_count = neutral_count = sarcasm_count = negative_percentage = 0
        
        # Create HTML body
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                }}
                .container {{
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 20px;
                }}
                .header {{
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    padding: 30px;
                    text-align: center;
                    border-radius: 10px 10px 0 0;
                }}
                .content {{
                    background: #f8f9fa;
                    padding: 30px;
                    border-radius: 0 0 10px 10px;
                }}
                .metric {{
                    display: inline-block;
                    width: 30%;
                    margin: 10px;
                    padding: 15px;
                    background: white;
                    border-radius: 10px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                    text-align: center;
                }}
                .metric-value {{
                    font-size: 24px;
                    font-weight: bold;
                    color: #667eea;
                }}
                .metric-label {{
                    font-size: 12px;
                    color: #666;
                    margin-top: 5px;
                }}
                .insight-card {{
                    background: white;
                    padding: 15px;
                    margin: 15px 0;
                    border-left: 4px solid #667eea;
                    border-radius: 5px;
                }}
                .severity-high {{ border-left-color: #ff4757; }}
                .severity-medium {{ border-left-color: #ffb347; }}
                .severity-low {{ border-left-color: #00ff88; }}
                .button {{
                    display: inline-block;
                    padding: 10px 20px;
                    background: #667eea;
                    color: white;
                    text-decoration: none;
                    border-radius: 5px;
                    margin-top: 20px;
                }}
                .footer {{
                    text-align: center;
                    padding: 20px;
                    font-size: 12px;
                    color: #666;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>📊 Business Reputation Report</h1>
                    <p>{report_type.capitalize()} Summary for {datetime.now().strftime('%B %d, %Y')}</p>
                </div>
                
                <div class="content">
                    <h2>Key Metrics</h2>
                    <div style="text-align: center;">
                        <div class="metric">
                            <div class="metric-value">{total_reviews}</div>
                            <div class="metric-label">Total Reviews</div>
                        </div>
                        <div class="metric">
                            <div class="metric-value" style="color: #ff4757;">{negative_count}</div>
                            <div class="metric-label">Negative Reviews</div>
                        </div>
                        <div class="metric">
                            <div class="metric-value" style="color: #00ff88;">{positive_count}</div>
                            <div class="metric-label">Positive Reviews</div>
                        </div>
                    </div>
                    
                    <div style="text-align: center; margin-top: 20px;">
                        <div class="metric">
                            <div class="metric-value">{neutral_count}</div>
                            <div class="metric-label">Neutral Reviews</div>
                        </div>
                        <div class="metric">
                            <div class="metric-value">{sarcasm_count}</div>
                            <div class="metric-label">Sarcastic Reviews</div>
                        </div>
                        <div class="metric">
                            <div class="metric-value">{negative_percentage:.1f}%</div>
                            <div class="metric-label">Negative Rate</div>
                        </div>
                    </div>
        """
        
        # Add insights if available
        if insights and 'problems' in insights:
            html += """
                    <h2>🎯 Critical Insights</h2>
            """
            
            for problem, suggestion, severity in zip(
                insights.get('problems', [])[:3],
                insights.get('suggestions', [])[:3],
                insights.get('severity', ['Medium']*3)
            ):
                severity_class = f"severity-{severity.lower()}"
                html += f"""
                    <div class="insight-card {severity_class}">
                        <strong>⚠️ Problem:</strong> {problem}<br>
                        <strong>💡 Solution:</strong> {suggestion}<br>
                        <strong>Priority:</strong> {severity}
                    </div>
                """
        
        # Add call to action
        html += f"""
                    <div style="text-align: center;">
                        <a href="#" class="button">View Full Dashboard</a>
                    </div>
                </div>
                
                <div class="footer">
                    <p>This is an automated report from your Business Reputation Monitoring System.</p>
                    <p>To unsubscribe or change frequency, please update your dashboard settings.</p>
                    <p>© {datetime.now().year} Business Reputation Monitor. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return html
    
    def generate_pdf_report(self):
        """Generate PDF report for attachment"""
        try:
            generator = PDFReportGenerator(company_name="Business Reputation Report")
            pdf_file = f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            generator.generate_report(pdf_file)
            return pdf_file
        except Exception as e:
            print(f"❌ PDF generation failed: {e}")
            return None
    
    def schedule_daily_report(self, recipient_email, time="09:00"):
        """Schedule daily report at specific time"""
        def job():
            self.send_report_email(recipient_email, "daily")
        
        schedule.every().day.at(time).do(job)
        job_id = f"daily_{recipient_email}_{time}"
        self.scheduled_jobs[job_id] = job
        print(f"✅ Daily report scheduled for {recipient_email} at {time}")
        return job_id
    
    def schedule_weekly_report(self, recipient_email, day="monday", time="09:00"):
        """Schedule weekly report on specific day"""
        def job():
            self.send_report_email(recipient_email, "weekly")
        
        # Map day to schedule method
        day_map = {
            'monday': schedule.every().monday,
            'tuesday': schedule.every().tuesday,
            'wednesday': schedule.every().wednesday,
            'thursday': schedule.every().thursday,
            'friday': schedule.every().friday,
            'saturday': schedule.every().saturday,
            'sunday': schedule.every().sunday
        }
        
        day_map.get(day.lower(), schedule.every().monday).at(time).do(job)
        job_id = f"weekly_{recipient_email}_{day}_{time}"
        self.scheduled_jobs[job_id] = job
        print(f"✅ Weekly report scheduled for {recipient_email} on {day}s at {time}")
        return job_id
    
    def run_scheduler(self):
        """Run the scheduler in background"""
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute

def test_email():
    """Test function for the local SMTP server"""
    print("📧 Email Reporter Test (Local SMTP)")
    print("="*50)
    print("\nMake sure Mailpit is running!")
    print("1. Mailpit should be open in a terminal window")
    print("2. Web UI is at: http://localhost:8025\n")
    
    # Use the local test configuration automatically
    reporter = EmailReporter()  # Will read from .env or use defaults
    
    recipient_email = input("Enter a test recipient email (e.g., admin@business.com): ")
    
    print("\n📤 Sending test email via local SMTP...")
    success = reporter.send_report_email(recipient_email, "test", include_pdf=True)
    
    if success:
        print("\n✅ Test email 'sent' successfully!")
        print("📧 Open http://localhost:8025 in your browser to view the email and PDF attachment.")
    else:
        print("\n❌ Failed to send email. Is Mailpit running?")

if __name__ == "__main__":
    test_email()