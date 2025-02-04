import streamlit as st
import os
import time
import pandas as pd
from datetime import datetime
from database.user_dao import (
    find_user, save_user, get_all_users, toggle_user_status, 
    find_users_by_name_pattern, update_user, reset_password
)
from utils.security import hash_password
from utils.session_manager import clear_session, load_session
import pymongo
from bson.objectid import ObjectId

# Connect to MongoDB
client = pymongo.MongoClient("mongodb://localhost:27017/")
db = client["adaptive_math_db"]
#students_collection = db["students"]

# Page configuration
st.set_page_config(
   page_title="Math Web App - Admin Dashboard", 
   page_icon="🔢", 
   layout="wide",
)

# Remove sidebar completely
st.markdown("""
    <style>
    [data-testid="stSidebar"], [data-testid="stSidebarNav"] {
        display: none !important;
    }
    .title-container {
        display: flex;
        justify-content: space-between;
        align-items: center;
        width: 100%;
    }
    .logout-button {
        background-color: red;
        color: white;
        padding: 8px 12px;
        border: none;
        border-radius: 5px;
        cursor: pointer;
        font-size: 16px;
    }
    </style>
""", unsafe_allow_html=True)

# Load session state
load_session()

# Redirect user to login if not logged in
if not st.session_state.logged_in:
    st.switch_page("pages/login_page.py")

# Logout function
def logout():
    clear_session()
    st.switch_page("pages/login_page.py")

# Display dashboard title with logout button (Only for Admins)
if st.session_state.user_role == "admin":
    col1, col2 = st.columns([0.9, 0.1])
    with col1:
        st.title("Admin Dashboard")
    with col2:
        st.button("Logout", on_click=logout, key="logout_button", help="Click to logout")

    # User Management Tabs
    # User Management Tabs (Now with 5 Tabs)
tab1, tab2, tab3, tab4, tab5 = st.tabs(["Add User", "Enable/Disable User", "Reset Password", "Update Email", "Show All Users"])


# ---------------------------------------
# TAB 1: Add New User
# ---------------------------------------
with tab1:
    st.header("Add New User")

    # Role selection outside form
    role = st.selectbox("Select Role", ["student", "teacher"], key="role_select")

    with st.form("add_user_form", clear_on_submit=True):
        name = st.text_input("Full Name")
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")

        parent_email = school = grade = None

        if role == "student":
            parent_email = st.text_input("Parent Email (Optional)")
            grade = st.selectbox("Grade", [str(i) for i in range(6, 13)])
            school = st.text_input("School Name")

        gender = st.selectbox("Gender", ["male", "female", "other"])

        submitted = st.form_submit_button("Add User")
        
        if submitted:
            if role == "student" and not parent_email:
                st.error("Parent email is required for student accounts")
            elif not all([name, email, password, role, gender]):
                st.error("Please fill in all fields")
            elif role == "student" and (not grade or not school):
                st.error("Please provide student details.")
            else:
                try:
                    new_user = {
                        "_id": ObjectId(),
                        "name": name,
                        "email": email.lower().strip(),
                        "parent_email": parent_email if parent_email else None,
                        "password_hash": hash_password(password),
                        "role": role,
                        "gender": gender,
                        "active": True,
                        "created_at": datetime.utcnow(),
                        "updated_at": datetime.utcnow()
                    }
                    
                    existing_user = find_user(email)
                    if existing_user:
                        st.error("Email already exists. Please use a different email.")
                    else:
                        if role == "student":
                            # Add grade and school to new_user for student role
                            new_user["grade"] = int(grade)
                            new_user["school"] = school

                        if save_user(new_user):
                            st.success(f"Successfully created new {role} account for {name}")
                        else:
                            st.error("Failed to create user. Please try again.")
                except Exception as e:
                    st.error(f"An error occurred: {str(e)}")


# ---------------------------------------
# TAB 2: Enable/Disable User
# ---------------------------------------
with tab2:
    st.header("Enable/Disable User")

    search_name = st.text_input("🔍 Search by name", key="disable_search")

    if search_name:
        users = find_users_by_name_pattern(search_name)
        if users:
            st.write(f"Found {len(users)} matching users:")
            for user in users:
                user_email = user['email']
                user_key = f"user_{user_email}"
                st.write(f"{user.get('name', 'Default User')} ({user_email})")
                st.write(f"Role: {user.get('role', 'student')}")

                current_status = user.get('active', True)
                st.write(f"Status: {'Active' if current_status else 'Disabled'}")

                new_status = not current_status
                button_text = "Disable User" if current_status else "Enable User"

                if st.button(button_text, key=f"toggle_{user_key}"):
                    try:
                        success = toggle_user_status(user_email, new_status)
                        if success:
                            status_text = "disabled" if current_status else "enabled"
                            st.success(f"Successfully {status_text} user: {user['name']} ({user_email})")
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
                                success = reset_password(user['email'], new_password)
                                if success:
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
# TAB 4: Update Email (Student or Parent)
# ---------------------------------------
with tab4:
    st.header("Update Email")

    search_name = st.text_input("🔍 Search by name", key="update_email_search")

    if search_name:
        users = find_users_by_name_pattern(search_name)
        if users:
            st.write(f"Found {len(users)} matching users:")
            
            for user in users:
                user_email = user['email']
                with st.expander(f"{user['name']} ({user_email})"):
                    st.write(f"Current Student Email: {user_email}")
                    st.write(f"Current Parent Email: {user.get('parent_email', 'N/A')}")
                    st.write(f"Role: {user.get('role', 'N/A')}")

                    # Assigning a unique key for each selectbox to avoid duplicate ID error
                    update_choice = st.selectbox(
                        "Select Email to Update", 
                        ["Student Email", "Parent Email"], 
                        key=f"update_choice_{user_email}"
                    )

                    # Input for new email with a unique key
                    new_email = st.text_input(
                        "New Email Address", 
                        key=f"new_email_{user_email}"
                    )

                    if st.button("Update Email", key=f"update_email_btn_{user_email}"):
                        if not new_email:
                            st.error("Please enter a new email address.")
                        else:
                            existing_user = find_user(new_email)
                            if existing_user and existing_user['email'].lower() != user['email'].lower():
                                st.error("This email address is already in use by another user.")
                            else:
                                update_data = {}
                                if update_choice == "Student Email":
                                    update_data["email"] = new_email.strip().lower()
                                elif update_choice == "Parent Email":
                                    update_data["parent_email"] = new_email.strip().lower()

                                update_data["updated_at"] = datetime.utcnow()

                                success = update_user_email(user_email, update_data)

                                if success:
                                    update_type = "Student" if update_choice == "Student Email" else "Parent"
                                    st.success(f"{update_type} Email successfully updated to {new_email}")
                                    time.sleep(1)
                                    st.rerun()
                                else:
                                    st.error("Failed to update email. Please try again.")
        else:
            st.warning("No users found matching your search.")



import pandas as pd

# ---------------------------------------
# TAB 5: Show All Users
# ---------------------------------------
with tab5:
    st.header("Show All Users")

    # Fetch all users
    users = get_all_users()  # Ensure it fetches 'parent_email'

    if users:
        total_users = len(users)
        st.subheader(f"Total Users: {total_users}")

        # Prepare data for display
        table_data = []
        for index, user in enumerate(users, start=1):
            table_data.append([
                user.get("name", "N/A"), 
                user.get("email", "N/A"), 
                user.get("parent_email", parent_email),  # NEW COLUMN
                user.get("role", "N/A"), 
                "✅ Active" if user.get("active", False) else "❌ Inactive"
            ])

        # Define column names (Removed Index)
        columns = ["Name", "Email", "Parent Email", "Role", "Status"]

        # Convert to DataFrame
        df = pd.DataFrame(table_data, columns=columns)

        # Display as an interactive table without index
        st.dataframe(df, use_container_width=True, hide_index=True)  

    else:
        st.warning("No users found in the system.")


