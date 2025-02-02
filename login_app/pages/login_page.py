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

st.markdown(
    """
    <style>
        section[data-testid="stSidebar"] {display: none !important;}
        [data-testid="collapsedControl"] {display: none !important;}
    </style>
    """,
    unsafe_allow_html=True
)

st.title("🔢 Math Web App - Login")

# ✅ Track app mode (Login, Forgot Password, Reset Password)
if "reset_mode" not in st.session_state:
    st.session_state.reset_mode = False  # Default: Show login form
if "reset_code_mode" not in st.session_state:
    st.session_state.reset_code_mode = False  # Show reset code form only when needed

# ✅ Forgot Password Form
if st.session_state.reset_mode:
    st.subheader("🔑 Reset Your Password")

    reset_email = st.text_input("Enter your registered email", placeholder="user@example.com")

    # ✅ Buttons: "Send Reset Code" & "Back to Login" on the same row
    col1, col2 = st.columns([1, 1])  
    with col1:
        send_reset_btn = st.button("Send Reset Code")
    with col2:
        back_to_login_btn = st.button("Back to Login")

    # ✅ Handle button clicks
    if send_reset_btn:
        with st.spinner("Verifying email..."):
            time.sleep(2)  # Simulate processing
            reset_code = save_reset_code(reset_email)  # ✅ Validate email & generate reset code
            
            if reset_code:
                st.session_state.reset_email = reset_email  # ✅ Store email in session
                st.session_state.reset_code_mode = True  # ✅ Move to next step
                st.session_state.reset_mode = False  # ✅ Hide email entry form
                st.rerun()
            else:
                st.error("This email is not registered. Please check and try again.")

    if back_to_login_btn:
        st.session_state.reset_mode = False  # ✅ Switch back to login
        st.rerun()

# ✅ Reset Code & New Password Form
elif st.session_state.reset_code_mode:
    st.subheader("🔑 Enter Reset Code & New Password")

    reset_code = st.text_input("Enter the reset code sent to your email")
    new_password = st.text_input("Enter new password", type="password", placeholder="New password")

    # ✅ Buttons: "Submit New Password" & "Back to Login"
    col1, col2 = st.columns([1, 1])  
    with col1:
        submit_password_btn = st.button("Submit New Password")
    with col2:
        cancel_reset_btn = st.button("Back to Login")

    # ✅ Handle Password Reset
    if submit_password_btn:
        with st.spinner("Verifying reset code..."):
            time.sleep(2)
            is_valid = verify_reset_code(st.session_state.reset_email, reset_code)

            if is_valid:
                update_password(st.session_state.reset_email, new_password)  # ✅ Update DB
                st.success("Password reset successful! You can now log in with your new password.")
                st.session_state.reset_code_mode = False  # ✅ Hide this form
                st.session_state.reset_mode = False
            else:
                st.error("Invalid or expired reset code. Please try again.")

    if cancel_reset_btn:
        st.session_state.reset_code_mode = False  # ✅ Back to login
        st.session_state.reset_mode = False
        st.rerun()

# ✅ Standard Login Form
else:
    st.markdown('<div class="login-container" style="width: 50%; margin: auto;">', unsafe_allow_html=True)

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

st.markdown("</div>", unsafe_allow_html=True)
