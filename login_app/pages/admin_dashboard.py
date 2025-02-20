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
import re
from st_aggrid import AgGrid, GridOptionsBuilder


if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_role = None
    st.session_state.user_email = None
    st.session_state.remember_me = False


def is_valid_email(email):
    """Check if the provided email follows a valid pattern."""
    email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(email_regex, email)

# Connect to MongoDB
client = pymongo.MongoClient("mongodb://localhost:27017/")
db = client["adaptive_math_db"]

# Page configuration
st.set_page_config(
   page_title="Math Web App - Admin Dashboard", 
   page_icon="🔢", 
   layout="centered",
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
    col1, col2 = st.columns([0.85, 0.15])
    with col1:
        st.title("Admin Dashboard")
    with col2:
        st.button("Logout", on_click=logout, key="logout_button", help="Click to logout")

# --------------------------------------------------
# Reordered Tabs
# --------------------------------------------------
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "Add User", 
    "Enable/Disable User", 
    "Reset Password", 
    "Show All Users",      # <--- 4th Tab
    "Update Phone",        # <--- 5th Tab
    "Update Email"         # <--- 6th Tab
])

# ---------------------------------------
# TAB 1: Add New User
# ---------------------------------------
with tab1:
    st.header("Add New User")

    role = st.selectbox("Select Role", ["student", "teacher"], key="role_select")

    with st.form("add_user_form", clear_on_submit=False):
        name = st.text_input("Full Name")
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")

        phone_label = "Parent Mobile Number" if role == "student" else "Teacher Mobile Number"
        phone = st.text_input(phone_label)

        parent_email = school = grade = None
        if role == "student":
            parent_email = st.text_input("Parent Email")
            grade = st.selectbox("Grade", [str(i) for i in range(6, 13)])
            school = st.text_input("School Name")

        gender = st.selectbox("Gender", ["male", "female", "other"])

        submitted = st.form_submit_button("Add User")
        if submitted:
            # Validate phone number field
            if not phone:
                st.error("Please fill in the phone number.")
            elif not phone.isdigit():
                st.error("Phone number can only contain digits.")
            elif not is_valid_email(email):
                st.error("Please enter a valid email address.")
            elif not all([name, email, password, role, gender]):
                st.error("Please fill in all required fields.")
            elif role == "student" and not parent_email:
                st.error("Parent email is required for student accounts.")
            else:
                # Proceed to build the new_user dictionary and save it
                new_user = {
                    "_id": ObjectId(),
                    "name": name,
                    "email": email.lower().strip(),
                    "password_hash": hash_password(password),
                    "role": role,
                    "gender": gender,
                    "active": True,
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow(),
                    "phone": phone
                }
                if role == "student":
                    new_user["parent_email"] = parent_email
                    new_user["grade"] = int(grade)
                    new_user["school"] = school

                existing_user = find_user(email)
                if existing_user:
                    st.error("Email already exists. Please use a different email.")
                else:
                    if save_user(new_user):
                        st.success(f"Successfully created new {role} account for {name}")
                    else:
                        st.error("Failed to create user. Please try again.")

# ---------------------------------------
# TAB 2: Enable/Disable User
# ---------------------------------------
with tab2:
    st.header("Enable/Disable User")

    search_name = st.text_input("🔍 Search by name", key="disable_search")

    if search_name:
        users = find_users_by_name_pattern(search_name)
        if users:
            # st.write(f"Found {len(users)} matching users:")
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
# TAB 4: Show All Users
# ---------------------------------------
with tab4:
    st.header("Show All Users")
    users = get_all_users()

    if users:
        total_users = len(users)
        st.subheader(f"Total Users: {total_users}")

        table_data = []
        for user in users:
            role = user.get("role", "N/A")
            table_data.append([
                user.get("name", "N/A"),
                user.get("email", "N/A"),
                user.get("parent_email", "N/A"),
                role,
                user.get("gender", "N/A"),
                str(user.get("grade", "N/A")) if role == "student" else "N/A",
                user.get("school", "N/A") if role == "student" else "N/A",
                user.get("phone", "N/A"),  
                "✅ Enabled" if user.get("active", False) else "❌ Disabled"
            ])

        columns = [
            "Name", 
            "Email", 
            "Parent Email", 
            "Role", 
            "Gender", 
            "Grade", 
            "School", 
            "Phone",
            "Status"
        ]

        df = pd.DataFrame(table_data, columns=columns)
        
        # Build Grid Options
        gb = GridOptionsBuilder.from_dataframe(df)
        gb.configure_pagination(paginationAutoPageSize=True)  
        gb.configure_side_bar()                               # Add a sidebar with filters
        gridOptions = gb.build()

        # Display interactive grid
        AgGrid(
            df,
            gridOptions=gridOptions,
            theme="streamlit",              # Other themes: "light", "dark", "blue", "fresh", "material"
            fit_columns_on_grid_load=True   # Auto-size columns to fit
        )


    else:
        st.warning("No users found in the system.")

# ---------------------------------------
# TAB 5: Update Phone
# ---------------------------------------
with tab5:
    st.header("Update Phone Number")

    search_name = st.text_input("🔍 Search by name", key="update_phone_search")
    
    if search_name:
        users = find_users_by_name_pattern(search_name)
        if users:
            st.write(f"Found {len(users)} matching users:")

            for user in users:
                user_email = user["email"]
                with st.expander(f"{user['name']} ({user_email})"):
                    current_phone = user.get("phone", "N/A")
                    st.write(f"**Current Phone:** {current_phone}")

                    new_phone = st.text_input(
                        "New Phone Number", 
                        key=f"new_phone_{user_email}"
                    )

                    if st.button("Update Phone", key=f"update_phone_btn_{user_email}"):
                        if not new_phone:
                            st.error("Please enter a new phone number.")
                        elif not new_phone.isdigit():
                            st.error("Phone number can only contain digits.")
                        else:
                            update_data = {
                                "phone": new_phone.strip(),
                                "updated_at": datetime.utcnow()
                            }
                            success = update_user(user_email, update_data)
                            if success:
                                st.success(f"Phone number updated to {new_phone} for {user['name']}")
                            else:
                                st.error("Failed to update phone number. Please try again.")
        else:
            st.warning("No users found matching your search.")

# ---------------------------------------
# TAB 6: Update Email
# ---------------------------------------
# TAB 6: Update Email
with tab6:
    st.header("Update Email")

    search_name = st.text_input("🔍 Search by name", key="update_email_search")

    if search_name:
        users = find_users_by_name_pattern(search_name)
        if users:
            st.write(f"Found {len(users)} matching users:")
            
            for user in users:
                user_email = user['email']
                role = user.get("role", "N/A")

                with st.expander(f"{user['name']} ({user_email})"):
                    # 1. Conditional labeling based on role
                    if role == "student":
                        st.write(f"Current Student Email: {user_email}")
                        st.write(f"Current Parent Email: {user.get('parent_email', 'N/A')}")
                    else:  # teacher
                        st.write(f"Current Teacher Email: {user_email}")

                    st.write(f"Role: {role}")

                    # 2. Conditional dropdown based on role
                    if role == "student":
                        update_options = ["Student Email", "Parent Email"]
                    else:
                        update_options = ["Teacher Email"]

                    update_choice = st.selectbox(
                        "Select Email to Update",
                        update_options,
                        key=f"update_choice_{user_email}"
                    )

                    # 3. Update logic
                    new_email = st.text_input(
                        "New Email Address", 
                        key=f"new_email_{user_email}"
                    )

                    if st.button("Update Email", key=f"update_email_btn_{user_email}"):
                        if not new_email:
                            st.error("Please enter a new email address.")
                        elif not is_valid_email(new_email):
                            st.error("Please enter a valid email address.")
                        else:
                            existing_user = find_user(new_email)
                            if existing_user and existing_user['email'].lower() != user['email'].lower():
                                st.error("This email address is already in use by another user.")
                            else:
                                update_data = {}
                                if update_choice == "Student Email" or update_choice == "Teacher Email":
                                    update_data["email"] = new_email.strip().lower()
                                elif update_choice == "Parent Email":
                                    update_data["parent_email"] = new_email.strip().lower()

                                update_data["updated_at"] = datetime.utcnow()

                                success = update_user(user_email, update_data)
                                if success:
                                    st.success(f"{update_choice} successfully updated to {new_email}")
                                    time.sleep(1)
                                else:
                                    st.error("Failed to update email. Please try again.")
        else:
            st.warning("No users found matching your search.")
