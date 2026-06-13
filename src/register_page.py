import streamlit as st
from firebase_auth import register_user

def show_register_page():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Sora:wght@300;400;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Sora', sans-serif; }

    .stApp {
        background: linear-gradient(135deg, #0f0c29 0%, #302b63 50%, #24243e 100%);
        min-height: 100vh;
    }
    .stTextInput > div > div > input {
        background: rgba(255,255,255,0.07) !important;
        border: 1px solid rgba(255,255,255,0.12) !important;
        border-radius: 10px !important;
        color: white !important;
        font-family: 'Sora', sans-serif !important;
    }
    .stTextInput > div > div > input:focus {
        border-color: #6366f1 !important;
        box-shadow: 0 0 0 2px rgba(99,102,241,0.2) !important;
    }
    .stTextInput label { color: rgba(255,255,255,0.6) !important; font-size: 0.85rem !important; }
    .stButton > button {
        background: linear-gradient(135deg, #6366f1, #8b5cf6) !important;
        color: white !important;
        border: none !important;
        border-radius: 12px !important;
        font-family: 'Sora', sans-serif !important;
        font-weight: 600 !important;
        font-size: 0.95rem !important;
        padding: 0.65rem !important;
        transition: all 0.2s !important;
    }
    .stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 25px rgba(99,102,241,0.4) !important;
    }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

    # Logo
    st.markdown("""
    <div style="text-align:center; padding: 2rem 0 1rem 0;">
        <div style="font-size:3rem">🎓</div>
        <div style="font-size:2rem; font-weight:700; background: linear-gradient(90deg, #a78bfa, #60a5fa, #34d399);
            -webkit-background-clip:text; -webkit-text-fill-color:transparent; background-clip:text;">
            UniGuide
        </div>
        <div style="color:rgba(255,255,255,0.45); font-size:0.85rem; margin-top:0.2rem; font-weight:300;">
            Create your free account
        </div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 1.6, 1])
    with col2:
        st.markdown("""
        <div style="background:rgba(255,255,255,0.05); border:1px solid rgba(255,255,255,0.1);
            border-radius:20px; padding:2rem; backdrop-filter:blur(20px);">
            <p style="color:#a78bfa; font-weight:700; font-size:1.15rem; text-align:center; margin-bottom:1.2rem;">
                📝 Create New Account
            </p>
        </div>
        """, unsafe_allow_html=True)

        full_name = st.text_input("Full Name", placeholder="Enter your full name", key="reg_fullname")
        email = st.text_input("Email Address", placeholder="Enter your email address", key="reg_email")
        username = st.text_input("Username", placeholder="Choose a username (min 3 characters)", key="reg_username")

        col_p1, col_p2 = st.columns(2)
        with col_p1:
            password = st.text_input("Password", type="password", placeholder="Min 6 characters", key="reg_password")
        with col_p2:
            confirm = st.text_input("Confirm Password", type="password", placeholder="Repeat password", key="reg_confirm")

        if st.button("Create Account →", use_container_width=True, key="register_btn"):
            if not all([full_name, email, username, password, confirm]):
                st.error("⚠️ Please fill in all fields!")
            elif password != confirm:
                st.error("❌ Passwords do not match!")
            else:
                with st.spinner("Creating your account..."):
                    success, message = register_user(
                        full_name.strip(),
                        email.strip(),
                        username.strip(),
                        password
                    )
                if success:
                    st.success(f"✅ {message}")
                    st.balloons()
                    import time
                    time.sleep(2)
                    st.session_state.current_page = "login"
                    st.rerun()
                else:
                    st.error(f"❌ {message}")

        st.markdown('<div style="height:1px; background:linear-gradient(90deg,transparent,rgba(255,255,255,0.1),transparent); margin:1.2rem 0;"></div>', unsafe_allow_html=True)

        st.markdown('<p style="color:rgba(255,255,255,0.4); font-size:0.82rem; text-align:center;">Already have an account?</p>', unsafe_allow_html=True)

        if st.button("← Back to Login", use_container_width=True, key="go_login_btn"):
            st.session_state.current_page = "login"
            st.rerun()
