#!/usr/bin/env python3
"""
Test the complete email reporting system
"""

import os
import sys
from email_reporter import EmailReporter
from pdf_report_generator import PDFReportGenerator

def check_prerequisites():
    """Check if all required files exist"""
    required_files = [
        'analyzed_reviews_optimized.csv',
        'insights.json'
    ]
    
    missing = []
    for file in required_files:
        if not os.path.exists(file):
            missing.append(file)
    
    if missing:
        print(f"❌ Missing files: {', '.join(missing)}")
        print("Please run sentiment_analyzer.py first")
        return False
    
    print("✅ All required files found")
    return True

def test_pdf_generation():
    """Test PDF generation"""
    print("\n📄 Testing PDF generation...")
    try:
        generator = PDFReportGenerator("Test Business")
        pdf_file = generator.generate_report("test_email_report.pdf")
        if os.path.exists("test_email_report.pdf"):
            print("✅ PDF generation successful")
            return True
        else:
            print("❌ PDF generation failed")
            return False
    except Exception as e:
        print(f"❌ PDF generation error: {e}")
        return False

def test_email_sending():
    """Test email sending with PDF attachment"""
    print("\n📧 Testing email sending...")
    
    # Get credentials
    sender_email = input("Your Gmail address: ")
    sender_password = input("Your App Password (16 chars): ")
    recipient_email = input("Recipient email address: ")
    
    reporter = EmailReporter(sender_email, sender_password)
    
    print("\n📤 Sending test report...")
    success = reporter.send_report_email(recipient_email, "test", include_pdf=True)
    
    if success:
        print("\n✅ Email sent successfully!")
        print("📧 Check the recipient's inbox (and spam folder)")
    else:
        print("\n❌ Email sending failed")
        print("Common issues:")
        print("1. Incorrect app password")
        print("2. 2FA not enabled on Google account")
        print("3. Less secure app access blocked")

def main():
    print("🚀 Email System Test Suite")
    print("="*50)
    
    if not check_prerequisites():
        sys.exit(1)
    
    if not test_pdf_generation():
        print("⚠️ Proceeding without PDF (email will still work)")
    
    test_email_sending()

if __name__ == "__main__":
    main()