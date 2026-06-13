import streamlit as st
from firebase_auth import login_user

def show_login_page():
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
    <div style="text-align:center; padding: 3rem 0 1.5rem 0;">
        <div style="font-size:3.5rem">🎓</div>
        <div style="font-size:2.2rem; font-weight:700; background: linear-gradient(90deg, #a78bfa, #60a5fa, #34d399);
            -webkit-background-clip:text; -webkit-text-fill-color:transparent; background-clip:text;">
            UniGuide
        </div>
        <div style="color:rgba(255,255,255,0.45); font-size:0.9rem; margin-top:0.3rem; font-weight:300;">
            West Bengal University Admission Assistant
        </div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 1.6, 1])
    with col2:
        # Card
        st.markdown("""
        <div style="background:rgba(255,255,255,0.05); border:1px solid rgba(255,255,255,0.1);
            border-radius:20px; padding:2rem; backdrop-filter:blur(20px);">
            <p style="color:#a78bfa; font-weight:700; font-size:1.15rem; text-align:center; margin-bottom:1.5rem;">
                🔐 Sign In to Your Account
            </p>
        </div>
        """, unsafe_allow_html=True)

        username = st.text_input("Username", placeholder="Enter your username", key="login_user")
        password = st.text_input("Password", type="password", placeholder="Enter your password", key="login_pass")

        if st.button("Login →", use_container_width=True, key="login_btn"):
            if not username.strip() or not password.strip():
                st.error("⚠️ Please fill in all fields!")
            else:
                with st.spinner("Signing in..."):
                    success, result, user_data = login_user(username.strip(), password)
                if success:
                    st.session_state.logged_in = True
                    st.session_state.username = username.strip()
                    st.session_state.user_name = result
                    st.session_state.user_email = user_data.get("email", "")
                    st.session_state.user_role = user_data.get("role", "student")
                    st.success(f"✅ Welcome, {result}!")
                    st.rerun()
                else:
                    st.error(f"❌ {result}")

        st.markdown('<div style="height:1px; background:linear-gradient(90deg,transparent,rgba(255,255,255,0.1),transparent); margin:1.2rem 0;"></div>', unsafe_allow_html=True)

        st.markdown('<p style="color:rgba(255,255,255,0.4); font-size:0.82rem; text-align:center;">Don\'t have an account?</p>', unsafe_allow_html=True)

        if st.button("📝 Create New Account", use_container_width=True, key="go_register"):
            st.session_state.current_page = "register"
            st.rerun()

    # Features
    st.markdown("""
    <div style="display:flex; gap:0.5rem; flex-wrap:wrap; justify-content:center; margin-top:1.5rem;">
        <span style="background:rgba(99,102,241,0.12); border:1px solid rgba(99,102,241,0.25);
            color:#a78bfa; padding:0.3rem 0.8rem; border-radius:20px; font-size:0.75rem;">🎓 3 Universities</span>
        <span style="background:rgba(99,102,241,0.12); border:1px solid rgba(99,102,241,0.25);
            color:#a78bfa; padding:0.3rem 0.8rem; border-radius:20px; font-size:0.75rem;">🤖 AI Powered</span>
        <span style="background:rgba(99,102,241,0.12); border:1px solid rgba(99,102,241,0.25);
            color:#a78bfa; padding:0.3rem 0.8rem; border-radius:20px; font-size:0.75rem;">📄 PDF Analysis</span>
        <span style="background:rgba(99,102,241,0.12); border:1px solid rgba(99,102,241,0.25);
            color:#a78bfa; padding:0.3rem 0.8rem; border-radius:20px; font-size:0.75rem;">⚖️ Course Compare</span>
    </div>
    """, unsafe_allow_html=True)
