import streamlit as st
import time
from database.db_connection import get_assignment_collection, get_user_collection, get_db, get_question_collection
from bson.objectid import ObjectId
from services.question_service import get_current_question, update_student_response
from services.student_service import get_assignment_progress, resume_assignment
from utils.session_manager import clear_session



# Authentication checks
if "logged_in" not in st.session_state or not st.session_state.logged_in:
    st.warning("You must be logged in to access this page.")
    st.switch_page("pages/login_page.py")

if st.session_state.get("user_role") != "student":
    st.error("Unauthorized Access! Redirecting...")
    st.switch_page("pages/login_page.py")

# Get user ID from email
users_collection = get_user_collection()
user_email = st.session_state.get("user_email")
user = users_collection.find_one({"email": user_email})

if not user:
    st.error("User not found. Please log in again.")
    st.switch_page("pages/login_page.py")

students_collection = get_db()["students"]
student = students_collection.find_one({"user_id": ObjectId(user["_id"])})
if not student:
    st.error("Student record not found. Please contact administrator.")
    st.switch_page("pages/login_page.py")

student_id = str(student["_id"])

# Fetch student details
student_name = user.get("name", "Student")

# UI Styling
st.markdown("""
    <style>
    .large-text { font-size: 24px !important; margin-bottom: 20px; }
    .question-text { font-size: 20px !important; margin-bottom: 15px; }
    .stRadio [role=radiogroup] label { font-size: 18px !important; margin: 10px 0; }
    .block-container { padding-top: 2rem; max-width: 1200px; }
    .option-feedback { display: inline-flex; align-items: center; margin-left: 10px; }
    .stRadio [role=radiogroup] { position: relative; }
    </style>
""", unsafe_allow_html=True)

col1, col2 = st.columns([0.7, 0.3])
with col1:
    st.title(f"Welcome, {student_name}! 👋")
with col2:
    if st.button("Logout", help="Click to logout"):
        clear_session()
        st.switch_page("pages/login_page.py")


progress_data = get_assignment_progress(student_id)

if progress_data:
    st.subheader("Assignment Progress")
    
    # Add headers
    header_cols = st.columns([1, 2, 1, 1, 1, 1])
    header_cols[0].markdown("**Topic**")
    header_cols[1].markdown("**Sub-topic**")
    header_cols[2].markdown("**Total**")
    header_cols[3].markdown("**Attempted**")
    header_cols[4].markdown("**Correct**")
    header_cols[5].markdown("**Action**")

    for idx, data in enumerate(progress_data):
        cols = st.columns([1, 2, 1, 1, 1, 1])
        cols[0].write(data["topic"])
        cols[1].write(data["sub_topic"])
        cols[2].write(data["total_questions"])
        cols[3].write(data["attempted"])
        cols[4].write(data["correct"])
        st.session_state["student_id"] = student_id
        if cols[5].button("Resume", key=f"resume_{idx}"):
            assignment_id = resume_assignment(student_id, data["topic"], data["sub_topic"])
            if assignment_id:
                st.session_state["current_assignment"] = assignment_id
                st.session_state["current_question_index"] = 0
                st.switch_page("pages/question_page.py")
else:
    st.info("No active assignments available.")