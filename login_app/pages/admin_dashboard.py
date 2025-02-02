import streamlit as st
import os
import time
from datetime import datetime
from database.user_dao import (
    find_user, 
    save_user, 
    delete_user, 
    toggle_user_status, 
    find_users_by_name_pattern,
    update_user
)
from utils.security import hash_password
from utils.session_manager import clear_session, load_session

# Page configuration
st.set_page_config(
    page_title="Math Web App - Admin Dashboard", 
    page_icon="🔢", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS 
st.markdown("""
    <style>
    /* Hide specifically the login page from sidebar */
    .css-1oe5cao {visibility: hidden;}
    
    /* Show main navigation items */
    div[data-testid="stSidebarNav"] {visibility: visible !important;}
    
    /* Container width control */
    .block-container {
        max-width: 800px;
        padding-top: 2rem;
        padding-right: 1rem;
        padding-left: 1rem;
        padding-bottom: 3rem;
    }
    
    /* Label styling */
    .stTextInput > label, .stSelectbox > label {
        font-size: 1.2rem;
        font-weight: 500;
        color: #333;
    }
    
    /* Input fields sizing */
    .stTextInput > div > div > input,
    .stSelectbox > div > div > div {
        max-width: 250px !important;
        min-width: 200px !important;
    }
    
    /* Password eye icon fix */
    .stTextInput > div > div {
        position: relative;
        display: flex;
        align-items: center;
    }
    
    .stTextInput button {
        position: absolute;
        right: 10px;
        top: 50%;
        transform: translateY(-50%);
    }
    
    /* Dropdown styling - Moving arrow to right end */
    .stSelectbox > div > div > div {
        position: relative;
    }
    
    .stSelectbox [data-baseweb="select"] {
        position: relative;
    }
    
    .stSelectbox [data-baseweb="icon"] {
        position: absolute;
        right: 0;
        top: 50%;
        transform: translateY(-50%);
    }
    
    /* Ensure dropdown text stays left-aligned */
    .stSelectbox [data-baseweb="select"] > div {
        text-align: left;
    }
    </style>
""", unsafe_allow_html=True)

# Load session state
load_session()

# Check if user is logged in and is admin
if not st.session_state.logged_in or st.session_state.user_role != "admin":
    st.switch_page("pages/login_page.py")

# Sidebar with logout
with st.sidebar:
    if st.button("Logout", key="logout_sidebar"):
        clear_session()

# Main content
st.title("Admin Dashboard")

# User Management Tabs
tab1, tab2, tab3, tab4 = st.tabs(["Add User", "Disable User", "Reset Password", "Update Email"])

# ---------------------------------------
# TAB 1: Add User
# ---------------------------------------
with tab1:
    st.header("Add New User")
    with st.form("add_user_form"):
        name = st.text_input("Full Name")
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        role = st.selectbox("Role", ["student", "teacher"])
        gender = st.selectbox("Gender", ["male", "female", "other"])
        
        submitted = st.form_submit_button("Add User")
        
        if submitted:
            if not all([name, email, password, role, gender]):
                st.error("Please fill in all fields")
            else:
                try:
                    new_user = {
                        "name": name,
                        "email": email.lower().strip(),
                        "password": hash_password(password),
                        "role": role,
                        "gender": gender,
                        "active": True,  # New users are active by default
                        "created_at": datetime.utcnow(),
                        "updated_at": datetime.utcnow()
                    }
                    
                    existing_user = find_user(email)
                    if existing_user:
                        st.error("Email already exists. Please use a different email.")
                    else:
                        if save_user(new_user):
                            st.success(f"Successfully created new {role} account for {name}")
                        else:
                            st.error("Failed to create user. Please try again.")
                except Exception as e:
                    st.error(f"An error occurred: {str(e)}")

# ---------------------------------------
# TAB 2: Disable User
# ---------------------------------------
with tab2:
    st.header("Disable User")
    
    # Search box
    search_name = st.text_input("🔍 Search by name", key="disable_search")
    
    if search_name:
        users = find_users_by_name_pattern(search_name)
        if users:
            st.write(f"Found {len(users)} matching users:")
            for user in users:
                user_key = f"user_{user['email']}"
                
                st.write(f"{user.get('name', 'Default User')} ({user['email']})")
                st.write(f"Role: {user.get('role', 'student')}")
                
                current_status = user.get('active', True)
                st.write(f"Status: {'Active' if current_status else 'Disabled'}")
                
                new_status = not current_status
                button_text = "Disable User" if current_status else "Enable User"
                
                if st.button(button_text, key=f"toggle_{user_key}"):
                    try:
                        success = toggle_user_status(user['email'], new_status)
                        if success:
                            status_text = "disabled" if current_status else "enabled"
                            st.success(f"Successfully {status_text} user: {user['name']} ({user['email']})")
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error("Failed to update user status.")
                    except Exception as e:
                        st.error(f"Error updating status: {str(e)}")
                
                st.divider()
        else:
            st.warning("No users found matching your search.")

# ---------------------------------------
# TAB 3: Reset Password
# ---------------------------------------
with tab3:
    st.header("Reset Password")
    
    search_name = st.text_input("🔍 Search by name", key="reset_search")
    
    if search_name:
        users = find_users_by_name_pattern(search_name)
        if users:
            st.write(f"Found {len(users)} matching users:")
            for user in users:
                with st.expander(f"{user['email']} - {user['name']}"):
                    st.write(f"Name: {user.get('name')}")
                    st.write(f"Role: {user.get('role')}")
                    
                    new_password = st.text_input(
                        "New Password",
                        type="password",
                        key=f"pwd_{user['email']}"
                    )

                    if st.button("Reset Password", key=f"reset_{user['email']}"):
                        if new_password:
                            try:
                                hashed_pass = hash_password(new_password)
                                update_success = update_user(user['email'], {"password": hashed_pass})
                                
                                if update_success:
                                    st.success(f"Password successfully reset for {user['email']}")
                                else:
                                    st.error("Failed to reset password. Please try again.")
                            except Exception as e:
                                st.error(f"An error occurred: {str(e)}")
                        else:
                            st.error("Please enter a new password")
        else:
            st.warning("No users found matching your search.")

# ---------------------------------------
# TAB 4: Update Email
# ---------------------------------------
with tab4:
    st.header("Update Email")

    # Search box
    search_name = st.text_input("🔍 Search by name", key="update_email_search")

    if search_name:
        users = find_users_by_name_pattern(search_name)
        if users:
            st.write(f"Found {len(users)} matching users:")
            
            # Only ONE expander per user
            for user in users:
                with st.expander(f"{user['name']} ({user['email']})"):
                    st.write(f"Current Email: {user['email']}")
                    st.write(f"Role: {user.get('role', 'N/A')}")

                    new_email = st.text_input(
                        "New Email Address", 
                        key=f"new_email_{user['email']}"
                    )

                    if st.button("Update Email", key=f"update_email_btn_{user['email']}"):
                        if not new_email:
                            st.error("Please enter a new email address.")
                        else:
                            # Check for uniqueness
                            existing_user = find_user(new_email)
                            if existing_user and existing_user['email'].lower() != user['email'].lower():
                                st.error("This email address is already in use by another user.")
                            else:
                                # Attempt the update
                                update_data = {
                                    "email": new_email.strip().lower(),
                                    "updated_at": datetime.utcnow()
                                }
                                success = update_user(user['email'], update_data)

                                if success:
                                    st.success(f"Email successfully updated to {new_email}")
                            
                                else:
                                    st.error("Failed to update email. Please try again.")
        else:
            st.warning("No users found matching your search.")
