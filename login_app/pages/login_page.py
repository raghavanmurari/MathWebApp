import streamlit as st
import time
import json
import os
import re
from services.auth_service import authenticate_user
from services.reset_service import save_reset_code, verify_reset_code, update_password

SESSION_FILE = "session_state.json"

def load_session():
    if os.path.exists(SESSION_FILE):
        with open(SESSION_FILE, "r") as f:
            session_data = json.load(f)
            st.session_state.logged_in = session_data.get("logged_in", False)
            st.session_state.user_role = session_data.get("user_role")
            st.session_state.user_email = session_data.get("user_email")
            st.session_state.remember_me = session_data.get("remember_me", False)

# Initialize session states if they don't exist
if 'reset_mode' not in st.session_state:
    st.session_state.reset_mode = False
if 'reset_code_mode' not in st.session_state:
    st.session_state.reset_code_mode = False
if 'reset_email' not in st.session_state:
    st.session_state.reset_email = ""
if 'new_password_mode' not in st.session_state:
    st.session_state.new_password_mode = False

load_session()

st.title("🔢 MAD")

st.markdown(
    """
    <h5 style="text-align: center;">
        ✨ Math A Day keeps errors at bay! ✨
    </h5>
    """,
    unsafe_allow_html=True
)


# Email validation pattern
email_pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"

def show_login_form():
    email = st.text_input("Email", placeholder="Enter your email (e.g., user@example.com)")
    password = st.text_input("Password", type="password", placeholder="Enter your password")
    remember_me = False  # Add this line instead
    
    col1, col2 = st.columns([1, 1])
    with col1:
        login_btn = st.button("Login")
    with col2:
        forgot_btn = st.button("Forgot Password?")

    handle_login(login_btn, email, password, remember_me)
    handle_forgot_password(forgot_btn)

def show_reset_email_form():
    st.subheader("Password Reset")
    st.write("Enter your email address to receive a reset code.")
    
    reset_email = st.text_input("Email", placeholder="Enter your email", key="reset_email_input")

    # Create two columns for the buttons
    
    col1, col2 = st.columns([1, 1])
    with col1:
        send_code_btn = st.button("Send Reset Code")
    with col2:
        back_btn = st.button("Back to Login")

    if send_code_btn and reset_email:
        if not re.match(email_pattern, reset_email):
            st.error("Invalid email format. Please enter a valid email.")
        else:
            with st.spinner("Sending reset code..."):
                if save_reset_code(reset_email):
                    st.session_state.reset_email = reset_email
                    st.session_state.reset_mode = False
                    st.session_state.reset_code_mode = True
                    st.success("Reset code sent! Check your email.")
                    st.rerun()
                else:
                    st.error("Failed to send reset code. Please try again or contact support.")

    if back_btn:
        st.session_state.reset_mode = False
        st.rerun()

def show_reset_code_form():
    st.subheader("Enter Reset Code")
    st.write("Please enter the 6-digit code sent to your email.")
    
    reset_code = st.text_input("Reset Code", max_chars=6, key="reset_code_input")
    # Create two columns for the buttons
    col1, col2 = st.columns([1, 1])
    with col1:
        verify_btn = st.button("Verify Code")
    with col2:
        back_btn = st.button("Back to Login")

    if verify_btn and reset_code:
        if verify_reset_code(st.session_state.reset_email, reset_code):
            st.session_state.reset_code_mode = False
            st.session_state.new_password_mode = True
            st.success("Code verified! Please set your new password.")
            st.rerun()
        else:
            st.error("Invalid or expired code. Please try again.")

    if back_btn:
        st.session_state.reset_code_mode = False
        st.session_state.reset_mode = False
        st.rerun()

def show_new_password_form():
    st.subheader("Set New Password")
    st.write("Please enter your new password.")
    
    new_password = st.text_input("New Password", type="password", key="new_password_input")
    confirm_password = st.text_input("Confirm Password", type="password", key="confirm_password_input")
        # Create two columns for the buttons
    col1, col2 = st.columns([1, 1])
    with col1:
        update_btn = st.button("Update Password")
    with col2:
        back_btn = st.button("Back to Login")

    if update_btn:
        if new_password != confirm_password:
            st.error("Passwords do not match!")

        else:
            success, message = update_password(st.session_state.reset_email, new_password)
            if success:
                st.success("Password updated successfully!")
                # Reset all password reset related states
                st.session_state.reset_mode = False
                st.session_state.reset_code_mode = False
                st.session_state.new_password_mode = False
                st.session_state.reset_email = ""
                time.sleep(2)
                st.rerun()
            else:
                st.error(f"Failed to update password: {message}")

    if back_btn:
        st.session_state.new_password_mode = False
        st.session_state.reset_mode = False
        st.session_state.reset_code_mode = False
        st.session_state.reset_email = ""
        st.rerun()

def handle_login(login_btn, email, password, remember_me):
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
                    
                    # NEW: Fetch and store the user's unique ID
                    from database.user_dao import find_user
                    user_record = find_user(email)
                    if user_record:
                        st.session_state.user_id = str(user_record["_id"])

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

def handle_forgot_password(forgot_btn):
    if forgot_btn:
        st.session_state.reset_mode = True
        st.rerun()

# Main flow control
if st.session_state.new_password_mode:
    show_new_password_form()
elif st.session_state.reset_code_mode:
    show_reset_code_form()
elif st.session_state.reset_mode:
    show_reset_email_form()
else:
    show_login_form()