import streamlit as st
import os
import json
from database.db_connection import get_user_collection  # ✅ Import DB connection

SESSION_FILE = "session_state.json"

def load_session():
    """Loads session state from file if it exists and ensures user_id is set."""
    if os.path.exists(SESSION_FILE):
        with open(SESSION_FILE, "r") as f:
            session_data = json.load(f)
            st.session_state.logged_in = session_data.get("logged_in", False)
            st.session_state.user_role = session_data.get("user_role")
            st.session_state.user_email = session_data.get("user_email")
            st.session_state.remember_me = session_data.get("remember_me", False)
            st.session_state.user_id = session_data.get("user_id")  # ✅ Ensure user_id is loaded

    # ✅ Fetch user_id if missing but user is logged in
    if st.session_state.get("logged_in") and "user_id" not in st.session_state:
        user_collection = get_user_collection()
        user = user_collection.find_one({"email": st.session_state.get("user_email")})
        if user:
            st.session_state.user_id = str(user["_id"])  # ✅ Store user_id in session

def save_session():
    """Saves session state to a file."""
    with open(SESSION_FILE, "w") as f:
        json.dump({
            "logged_in": st.session_state.logged_in,
            "user_role": st.session_state.user_role,
            "user_email": st.session_state.user_email,
            "remember_me": st.session_state.remember_me,
            "user_id": st.session_state.get("user_id")  # ✅ Ensure user_id is saved
        }, f)

def clear_session():
    """Ensure all session variables are reset on logout."""
    # st.write("DEBUG: Clearing session...")
    # Remove session file if it exists
    if os.path.exists(SESSION_FILE):
        os.remove(SESSION_FILE)
        
    # Clear all relevant session state variables
    session_keys = ["logged_in", "user_id", "user_role", "user_email", "remember_me"]
    for key in session_keys:
        if key in st.session_state:
            del st.session_state[key]
            
    # Set defaults
    st.session_state.logged_in = False
    st.session_state.user_id = None
    st.session_state.user_role = None
    st.session_state.remember_me = False
    st.rerun()  # Ensure Streamlit reloads with a fresh session
