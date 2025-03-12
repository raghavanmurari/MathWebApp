import streamlit as st
import time
from database.db_connection import get_assignment_collection, get_user_collection, get_db, get_question_collection
from bson.objectid import ObjectId
from services.question_service import get_current_question, update_student_response
from services.student_service import get_assignment_progress, resume_assignment
from utils.session_manager import clear_session

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_role = None
    st.session_state.user_email = None
    st.session_state.remember_me = False
    
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
student = students_collection.find_one({"user_id": ObjectId(user["_id"])});
if not student:
    st.error("Student record not found. Please contact administrator.")
    st.switch_page("pages/login_page.py")

student_id = str(student["_id"])

# Fetch student details
student_name = user.get("name", "Student")

# UI Styling
st.markdown("""
    <style>
    .logout-button > button {
        position: fixed !important;
        top: 20px !important;
        right: 20px !important;
    }
    .card {
        border-radius: 10px;
        padding: 15px;
        margin: 10px 0;
        background-color: #f9f9f9;
        box-shadow: 0px 2px 10px rgba(0, 0, 0, 0.1);
    }
    </style>
""", unsafe_allow_html=True)

col1, col2 = st.columns([0.7, 0.3])

with col1:
    st.markdown(f"<h1 style='margin-top:-30px;'>Welcome, {student_name}! 👋</h1>", unsafe_allow_html=True)
with col2:
    if st.button("Logout", help="Click to logout"):
        clear_session()
        st.switch_page("pages/login_page.py")

def display_assignment(data, student_id):
    # Create an expander title using key info
    expander_title = f"{data['topic']} | {data['sub_topic']} | Deadline: {data['deadline']}"
    
    # Use an expander to hide detailed info until clicked
    with st.expander(expander_title):
        st.markdown(
            f"<p style='font-size:16px;'>"
            f"<b>Total Questions:</b> {data['total_questions']} | "
            f"<b>Attempted:</b> {data['attempted']} | "
            f"<b>Correct:</b> {data['correct']}</p>",
            unsafe_allow_html=True
        )
        # Display the progress bar
        progress = int((data['attempted'] / data['total_questions']) * 100) if data['total_questions'] else 0
        st.progress(progress / 100)
        
        # Use the assignment_id to ensure the button key is unique
        unique_key_resume = f"resume_{data['assignment_id']}"
        unique_key_review = f"review_{data['assignment_id']}"
        
        # Show Resume button only if assignment is in progress
        is_completed = data['total_questions'] == data['attempted']
        if not is_completed:
            if st.button("▶ Resume", key=unique_key_resume, help="Continue where you left off"):
                assignment_id = resume_assignment(student_id, data["topic"], data["sub_topic"])
                if assignment_id:
                    st.session_state["student_id"] = student_id
                    st.session_state["current_assignment"] = assignment_id
                    st.session_state["current_question_index"] = 0
                    st.session_state["current_topic"] = data["topic"]
                    st.session_state["current_subtopic"] = data["sub_topic"]
                    st.switch_page("pages/question_page.py")
        
        # Show Review button if at least one question has been attempted
        if data['attempted'] > 0:
            if st.button("Review", key=unique_key_review, help="Review attempted questions"):
                assignment_id = data["assignment_id"]
                st.session_state["student_id"] = student_id
                st.session_state["current_assignment"] = assignment_id
                st.switch_page("pages/review_page.py")


progress_data = get_assignment_progress(student_id)

if progress_data:
    # Group assignments based on status
    completed_assignments = [data for data in progress_data if data['total_questions'] == data['attempted']]
    in_progress_assignments = [data for data in progress_data if data['total_questions'] != data['attempted']]

    # Add a single header for In Progress assignments
    if in_progress_assignments:
        # For the "In Progress" section
        st.markdown("""
            <h2 style="
                color: #c97b00; 
                background-color: #fff8e6; 
                padding: 10px 15px; 
                border-radius: 8px; 
                border-left: 5px solid #ffc107;
                display: inline-block;
                font-size: 20px;
                margin-bottom: 15px;
            ">
            ⏳ In Progress
            </h2>
        """, unsafe_allow_html=True)
    for data in in_progress_assignments:
        display_assignment(data, student_id)

    # Add a single header for Completed assignments
    if completed_assignments:
        # For the "Completed" section
        st.markdown("""
            <h2 style="
                color: #1e7e34; 
                background-color: #edf7ee; 
                padding: 10px 15px; 
                border-radius: 8px; 
                border-left: 5px solid #28a745;
                display: inline-block;
                font-size: 20px;
                margin-bottom: 15px;
            ">
            ✅ Completed
            </h2>
        """, unsafe_allow_html=True)
    for data in completed_assignments:
        display_assignment(data, student_id)

else:
    st.info("No active assignments available.")