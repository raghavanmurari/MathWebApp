import streamlit as st
from utils.session_manager import load_session, clear_session
from utils.navigation import redirect_to_dashboard, redirect_to_login

from config import get_db

# Diagnostic block to check DB connection
try:
    db = get_db()
    # Attempt a simple query, e.g., list collections or fetch one document
    collections = db.list_collection_names()
    st.write("Connected to DB! Collections:", collections)
except Exception as e:
    st.write("Error connecting to DB:", e)

# Simple page config with just the basics
st.set_page_config(
    page_title="Math Web Apppppppp",
    page_icon="🔢",
    layout="centered",
    initial_sidebar_state="collapsed"  # or "auto" or "expanded"
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