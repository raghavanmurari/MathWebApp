import streamlit as st
import time
import json
import os
from services.auth_service import authenticate_user
from services.reset_service import save_reset_code, verify_reset_code, update_password  # ✅ New imports

SESSION_FILE = "session_state.json"  # Persistent session storage

# ✅ Function to load session state
def load_session():
    if os.path.exists(SESSION_FILE):
        with open(SESSION_FILE, "r") as f:
            session_data = json.load(f)
            st.session_state.logged_in = session_data.get("logged_in", False)
            st.session_state.user_role = session_data.get("user_role")
            st.session_state.user_email = session_data.get("user_email")
            st.session_state.remember_me = session_data.get("remember_me", False)

# ✅ Load session (if "Remember Me" was enabled)
load_session()

# ✅ Hide Sidebar Immediately
st.set_page_config(page_title="Math Web App - Login", page_icon="🔢", layout="centered", initial_sidebar_state="collapsed")

st.title("🔢 Math Web App - Login")

# ✅ Standard Login Form
email = st.text_input("Email", placeholder="Enter your email (e.g., user@example.com)")
password = st.text_input("Password", type="password", placeholder="Enter your password")

# ✅ "Remember Me" Checkbox
remember_me = st.checkbox("Remember Me", value=st.session_state.remember_me)

# Validate Email Format
import re
email_pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"

# ✅ Buttons: Login & Forgot Password
col1, col2 = st.columns([1, 1])
with col1:
    login_btn = st.button("Login")
with col2:
    forgot_btn = st.button("Forgot Password?")

# ✅ Handle Login
if login_btn:
    if not re.match(email_pattern, email):
        st.error("Invalid email format. Please enter a valid email.")
    else:
        with st.spinner("Checking credentials..."):
            time.sleep(2)
            role = authenticate_user(email, password)


            if role == "disabled":
                st.error("This account has been disabled. Please contact your administrator.")
            elif role:
                st.session_state.logged_in = True
                st.session_state.user_role = role
                st.session_state.user_email = email
                st.session_state.remember_me = remember_me

                if remember_me:
                    with open(SESSION_FILE, "w") as f:
                        json.dump({
                            "logged_in": True,
                            "user_role": role,
                            "user_email": email,
                            "remember_me": remember_me
                        }, f)

                st.success(f"Login successful! Redirecting to {role} dashboard...")


                if role == "student":
                    st.switch_page("pages/student_dashboard.py")
                elif role == "teacher":
                    st.switch_page("pages/teacher_dashboard.py")
                elif role == "admin":
                    st.switch_page("pages/admin_dashboard.py")
            else:
                st.error("Invalid email or password. Please try again.")

# ✅ Handle Forgot Password Click
if forgot_btn:
    st.session_state.reset_mode = True  # ✅ Switch to "Forgot Password" mode
    st.session_state.reset_code_mode = False
    st.rerun()  # ✅ Refresh to show the reset form
