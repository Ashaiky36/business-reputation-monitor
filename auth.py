import sqlite3
import hashlib
import re
from datetime import datetime
import streamlit as st

class AuthSystem:
    def __init__(self, db_path="users.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize SQLite database with users table"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                full_name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                business_name TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def hash_password(self, password):
        """Hash password using SHA-256"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def validate_email(self, email):
        """Validate email format"""
        pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
        return re.match(pattern, email) is not None
    
    def validate_password(self, password):
        """Validate password strength"""
        if len(password) < 6:
            return False, "Password must be at least 6 characters"
        return True, "OK"
    
    def signup(self, full_name, email, password, business_name=""):
        """Register a new user"""
        # Validate inputs
        if not full_name or not email or not password:
            return False, "All fields are required"
        
        if not self.validate_email(email):
            return False, "Invalid email format"
        
        valid, msg = self.validate_password(password)
        if not valid:
            return False, msg
        
        # Check if user already exists
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
        if cursor.fetchone():
            conn.close()
            return False, "Email already registered"
        
        # Insert new user
        password_hash = self.hash_password(password)
        cursor.execute('''
            INSERT INTO users (full_name, email, password_hash, business_name)
            VALUES (?, ?, ?, ?)
        ''', (full_name, email, password_hash, business_name))
        
        conn.commit()
        user_id = cursor.lastrowid
        conn.close()
        
        return True, "Registration successful", user_id
    
    def login(self, email, password):
        """Authenticate user login"""
        if not email or not password:
            return False, "Email and password required"
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        password_hash = self.hash_password(password)
        cursor.execute('''
            SELECT id, full_name, email, business_name FROM users 
            WHERE email = ? AND password_hash = ?
        ''', (email, password_hash))
        
        user = cursor.fetchone()
        
        if user:
            # Update last login
            cursor.execute('''
                UPDATE users SET last_login = ? WHERE id = ?
            ''', (datetime.now(), user[0]))
            conn.commit()
            conn.close()
            
            return True, "Login successful", {
                'id': user[0],
                'full_name': user[1],
                'email': user[2],
                'business_name': user[3]
            }
        else:
            conn.close()
            return False, "Invalid email or password", None
    
    def get_user_by_email(self, email):
        """Get user information by email"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, full_name, email, business_name, created_at, last_login
            FROM users WHERE email = ?
        ''', (email,))
        
        user = cursor.fetchone()
        conn.close()
        
        if user:
            return {
                'id': user[0],
                'full_name': user[1],
                'email': user[2],
                'business_name': user[3],
                'created_at': user[4],
                'last_login': user[5]
            }
        return None

# Session state management
def init_session_state():
    """Initialize session state for authentication"""
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'user' not in st.session_state:
        st.session_state.user = None
    if 'auth_page' not in st.session_state:
        st.session_state.auth_page = 'login'  # login or signup

def login_screen():
    """Display login screen"""
    st.markdown("""
    <style>
    .auth-container {
        max-width: 450px;
        margin: 0 auto;
        padding: 2rem;
        background: white;
        border-radius: 15px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.1);
    }
    .auth-title {
        text-align: center;
        margin-bottom: 2rem;
    }
    .auth-title h1 {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 2rem;
        margin-bottom: 0;
    }
    .auth-title p {
        color: #666;
        font-size: 0.9rem;
    }
    </style>
    """, unsafe_allow_html=True)
    
    st.markdown('<div class="auth-container">', unsafe_allow_html=True)
    
    st.markdown('<div class="auth-title">', unsafe_allow_html=True)
    st.markdown("<h1>🔐 Business Reputation Monitor</h1>", unsafe_allow_html=True)
    st.markdown("<p>Secure Access to Your Dashboard</p>", unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Toggle between Login and Signup - Add unique keys
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Login", use_container_width=True, 
                    type="primary" if st.session_state.auth_page == 'login' else "secondary",
                    key="auth_login_tab"):
            st.session_state.auth_page = 'login'
            st.rerun()
    with col2:
        if st.button("Sign Up", use_container_width=True, 
                    type="primary" if st.session_state.auth_page == 'signup' else "secondary",
                    key="auth_signup_tab"):
            st.session_state.auth_page = 'signup'
            st.rerun()
    
    st.markdown("---")
    
    if st.session_state.auth_page == 'login':
        # Login Form
        email = st.text_input("Email Address", placeholder="business@example.com", key="login_email_input")
        password = st.text_input("Password", type="password", placeholder="Enter your password", key="login_password_input")
        
        if st.button("Login", type="primary", use_container_width=True, key="login_submit_button"):
            if email and password:
                auth = AuthSystem()
                success, message, user = auth.login(email, password)
                
                if success:
                    st.session_state.authenticated = True
                    st.session_state.user = user
                    st.success(message)
                    st.rerun()
                else:
                    st.error(message)
            else:
                st.warning("Please enter both email and password")
        
        st.markdown("---")
        st.caption("Demo Account: demo@business.com / demo123")
        
    else:
        # Signup Form
        full_name = st.text_input("Full Name", placeholder="John Doe", key="signup_name_input")
        email = st.text_input("Email Address", placeholder="business@example.com", key="signup_email_input")
        password = st.text_input("Password", type="password", placeholder="Min 6 characters", key="signup_password_input")
        confirm_password = st.text_input("Confirm Password", type="password", placeholder="Re-enter password", key="signup_confirm_input")
        business_name = st.text_input("Business Name (Optional)", placeholder="Your Company Name", key="signup_business_input")
        
        if st.button("Create Account", type="primary", use_container_width=True, key="signup_submit_button"):
            if password != confirm_password:
                st.error("Passwords do not match")
            elif full_name and email and password:
                auth = AuthSystem()
                success, message, user_id = auth.signup(full_name, email, password, business_name)
                
                if success:
                    st.success(message)
                    st.info("Please login with your credentials")
                    st.session_state.auth_page = 'login'
                    st.rerun()
                else:
                    st.error(message)
            else:
                st.warning("Please fill in all required fields")
    
    st.markdown('</div>', unsafe_allow_html=True)

# def login_screen():
#     """Display login screen"""
    
#     # Center the login container using Streamlit columns (more reliable than custom CSS)
#     st.markdown("<br><br>", unsafe_allow_html=True)
    
#     col1, col2, col3 = st.columns([1, 2, 1])
    
#     with col2:
#         # Simple white container without complex CSS
#         st.markdown("""
#         <div style="background-color: white; padding: 2rem; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
#         </div>
#         """, unsafe_allow_html=True)
        
#         st.markdown("""
#         <div style="text-align: center; margin-bottom: 2rem;">
#             <h1 style="color: #667eea;">🔐 Business Reputation Monitor</h1>
#             <p style="color: #666;">Secure Access to Your Dashboard</p>
#         </div>
#         """, unsafe_allow_html=True)
        
#         # Toggle between Login and Signup
#         tab1, tab2 = st.tabs(["🔑 Login", "📝 Sign Up"])
        
#         with tab1:
#             # Login Form
#             email = st.text_input("Email Address", placeholder="business@example.com", key="login_email_input")
#             password = st.text_input("Password", type="password", placeholder="Enter your password", key="login_password_input")
            
#             if st.button("Login", type="primary", use_container_width=True, key="login_submit_button"):
#                 if email and password:
#                     auth = AuthSystem()
#                     success, message, user = auth.login(email, password)
                    
#                     if success:
#                         st.session_state.authenticated = True
#                         st.session_state.user = user
#                         st.success(message)
#                         st.rerun()
#                     else:
#                         st.error(message)
#                 else:
#                     st.warning("Please enter both email and password")
            
#             st.markdown("---")
#             st.caption("Demo Account: demo@business.com / demo123")
        
#         with tab2:
#             # Signup Form
#             full_name = st.text_input("Full Name", placeholder="John Doe", key="signup_name_input")
#             email = st.text_input("Email Address", placeholder="business@example.com", key="signup_email_input")
#             password = st.text_input("Password", type="password", placeholder="Min 6 characters", key="signup_password_input")
#             confirm_password = st.text_input("Confirm Password", type="password", placeholder="Re-enter password", key="signup_confirm_input")
#             business_name = st.text_input("Business Name (Optional)", placeholder="Your Company Name", key="signup_business_input")
            
#             if st.button("Create Account", type="primary", use_container_width=True, key="signup_submit_button"):
#                 if password != confirm_password:
#                     st.error("Passwords do not match")
#                 elif full_name and email and password:
#                     auth = AuthSystem()
#                     success, message, user_id = auth.signup(full_name, email, password, business_name)
                    
#                     if success:
#                         st.success(message)
#                         st.info("Please login with your credentials")
#                         st.rerun()
#                     else:
#                         st.error(message)
#                 else:
#                     st.warning("Please fill in all required fields")
    
#     st.markdown("<br><br>", unsafe_allow_html=True)

def logout():
    """Logout user"""
    st.session_state.authenticated = False
    st.session_state.user = None
    st.session_state.app_stage = 'setup'
    st.rerun()