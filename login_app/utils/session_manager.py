import streamlit as st
import os
import json

SESSION_FILE = "session_state.json"

def load_session():
    """Loads session state from file if it exists."""
    if os.path.exists(SESSION_FILE):
        with open(SESSION_FILE, "r") as f:
            session_data = json.load(f)
            st.session_state.logged_in = session_data.get("logged_in", False)
            st.session_state.user_role = session_data.get("user_role")
            st.session_state.user_email = session_data.get("user_email")
            st.session_state.remember_me = session_data.get("remember_me", False)

def save_session():
    """Saves session state to a file."""
    with open(SESSION_FILE, "w") as f:
        json.dump({
            "logged_in": st.session_state.logged_in,
            "user_role": st.session_state.user_role,
            "user_email": st.session_state.user_email,
            "remember_me": st.session_state.remember_me
        }, f)

def clear_session():
    """Clears session state and logs the user out."""
    st.session_state.logged_in = False
    st.session_state.user_role = None
    st.session_state.user_email = None
    st.session_state.remember_me = False
    
    if os.path.exists(SESSION_FILE):
        os.remove(SESSION_FILE)  # ✅ Delete session file

    st.rerun()  # ✅ Force page refresh
