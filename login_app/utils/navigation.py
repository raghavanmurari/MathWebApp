import streamlit as st

def redirect_to_dashboard():
    """Redirects logged-in users to their respective dashboards."""
    if st.session_state.logged_in:
        if st.session_state.user_role == "student":
            st.switch_page("pages/student_dashboard.py")
        elif st.session_state.user_role == "teacher":
            st.switch_page("pages/teacher_dashboard.py")
        elif st.session_state.user_role == "admin":
            st.switch_page("pages/admin_dashboard.py")

def redirect_to_login():
    """Redirects the user to the login page if not logged in."""
    st.switch_page("pages/login_page.py")

