import streamlit as st
from utils.session_manager import load_session, clear_session
from utils.navigation import redirect_to_dashboard, redirect_to_login

from config import get_db

# Simple page config with just the basics
st.set_page_config(
    page_title="Math Web App",
    page_icon="🔢",
    layout="centered",
    initial_sidebar_state="collapsed"  # or "auto" or "expanded"
)

# Immediately inject CSS to hide the sidebar
st.markdown(
    """
    <style>
    [data-testid="collapsedControl"] {
        display: none;
    }
    </style>
    """,
    unsafe_allow_html=True
)
# Initialize session state if not already set
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_role = None
    st.session_state.user_email = None
    st.session_state.remember_me = False

# Load session if it exists
load_session()

# Check if the user requested to log out
if "logout" in st.query_params:
    clear_session()

# Redirect users based on login status
if st.session_state.logged_in:
    redirect_to_dashboard()
else:
    redirect_to_login()