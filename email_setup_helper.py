import os
import getpass
import json

def setup_email_config():
    """Interactive email configuration setup"""
    print("\n📧 Email Configuration Setup")
    print("="*50)
    print("\nFor Gmail, you need to:")
    print("1. Enable 2-Factor Authentication on your Google account")
    print("2. Generate an App Password: https://myaccount.google.com/apppasswords")
    print("3. Select 'Mail' and 'Windows Computer'")
    print("4. Copy the 16-character password\n")
    
    config = {}
    
    sender_email = input("Enter your Gmail address: ")
    config['SENDER_EMAIL'] = sender_email
    
    sender_password = getpass.getpass("Enter your App Password (16 characters): ")
    config['SENDER_PASSWORD'] = sender_password
    
    # Optional: Save to .env file
    save_config = input("\nSave configuration to .env file? (yes/no): ").lower()
    
    if save_config in ['yes', 'y']:
        with open('.env', 'w') as f:
            f.write(f"SENDER_EMAIL={config['SENDER_EMAIL']}\n")
            f.write(f"SENDER_PASSWORD={config['SENDER_PASSWORD']}\n")
        print("\n✅ Configuration saved to .env file")
        print("⚠️  Make sure to add .env to .gitignore!")
    
    return config

def test_email_connection():
    """Test email connection"""
    from email_reporter import EmailReporter
    
    # Load from .env if exists
    if os.path.exists('.env'):
        with open('.env', 'r') as f:
            for line in f:
                if '=' in line:
                    key, value = line.strip().split('=', 1)
                    os.environ[key] = value
    
    sender_email = os.getenv('SENDER_EMAIL')
    sender_password = os.getenv('SENDER_PASSWORD')
    
    if not sender_email or not sender_password:
        print("❌ Email configuration not found. Run setup first.")
        return False
    
    reporter = EmailReporter(sender_email, sender_password)
    recipient = input("Enter test recipient email: ")
    
    print("\n📤 Sending test email...")
    success = reporter.send_report_email(recipient, "test", include_pdf=False)
    
    if success:
        print("\n✅ Email configuration working!")
    else:
        print("\n❌ Email configuration failed. Check your app password.")
    
    return success

if __name__ == "__main__":
    print("🚀 Email Setup Helper")
    print("="*50)
    
    choice = input("1. Setup new configuration\n2. Test existing configuration\nChoice: ")
    
    if choice == '1':
        setup_email_config()
    elif choice == '2':
        test_email_connection()
    else:
        print("Invalid choice")