from auth import AuthSystem

def setup_demo_users():
    """Create demo users for testing"""
    auth = AuthSystem()
    
    # Demo users
    users = [
        {
            'full_name': 'Demo User',
            'email': 'demo@business.com',
            'password': 'demo123',
            'business_name': 'Demo Company'
        },
        {
            'full_name': 'John Smith',
            'email': 'john@techcorp.com',
            'password': 'tech123',
            'business_name': 'TechCorp Solutions'
        },
        {
            'full_name': 'Sarah Johnson',
            'email': 'sarah@retailstore.com',
            'password': 'retail123',
            'business_name': 'Retail Store Inc'
        }
    ]
    
    for user in users:
        success, message, user_id = auth.signup(
            user['full_name'],
            user['email'],
            user['password'],
            user['business_name']
        )
        
        if success:
            print(f"✅ Created user: {user['email']} (Password: {user['password']})")
        else:
            print(f"⚠️ {message} for {user['email']}")

if __name__ == "__main__":
    print("🔐 Setting up demo users...")
    setup_demo_users()
    print("\n📋 Demo Accounts Created:")
    print("   Email: demo@business.com | Password: demo123")
    print("   Email: john@techcorp.com | Password: tech123")
    print("   Email: sarah@retailstore.com | Password: retail123")