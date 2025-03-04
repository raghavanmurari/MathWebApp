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
    # Determine status and corresponding color
    is_completed = data['total_questions'] == data['attempted']
    status = "✔ Completed" if is_completed else "In Progress"
    status_color = "#28a745" if is_completed else "#ffc107"
    
    # Create an expander title using key info
    expander_title = f"{data['topic']} | {data['sub_topic']} | Deadline: {data['deadline']}"
    
    # Display a colored status header above the expander
    st.markdown(
        f"<div style='font-size:16px; margin-bottom:-10px;'>"
        f"<strong style='color:{status_color};'>{status}</strong></div>",
        unsafe_allow_html=True
    )
    
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
    # st.subheader("Assignment Progress")
    
    # First, group your assignments based on status.
    # Group assignments based on status
    completed_assignments = [data for data in progress_data if data['total_questions'] == data['attempted']]
    in_progress_assignments = [data for data in progress_data if data['total_questions'] != data['attempted']]

    # st.markdown("<h3>In Progress Assignments</h3>", unsafe_allow_html=True)
    for data in in_progress_assignments:
        display_assignment(data, student_id)

    # st.markdown("<h3>Completed Assignments</h3>", unsafe_allow_html=True)
    for data in completed_assignments:
        display_assignment(data, student_id)

    # for idx, data in enumerate(progress_data):
    #     # Determine completion status and corresponding color
    #     is_completed = data['total_questions'] == data['attempted']
    #     status = "✔ Completed" if is_completed else "In Progress"
    #     status_color = "#28a745" if is_completed else "#ffc107"  # green for completed, amber for in progress
        
    #     # Build a summary title for the expander (without colored HTML)
    #     expander_title = f"{data['topic']} | {data['sub_topic']} | Deadline: {data['deadline']}"
        
    #     # Display a colored header for the status
    #     st.markdown(
    #         f"<div style='font-size:16px; margin-bottom:-10px;'>"
    #         f"<strong style='color:{status_color};'>{status}</strong></div>",
    #         unsafe_allow_html=True
    #     )
        
    #     # Use an expander for detailed information
    #     with st.expander(expander_title):
    #         st.markdown('<div class="card">', unsafe_allow_html=True)
            
    #         st.markdown(
    #             f"<p style='font-size:16px;'>"
    #             f"<b>Total Questions:</b> {data['total_questions']} &nbsp;&nbsp;|&nbsp;&nbsp; "
    #             f"<b>Attempted:</b> {data['attempted']} &nbsp;&nbsp;|&nbsp;&nbsp; "
    #             f"<b>Correct:</b> {data['correct']}</p>", 
    #             unsafe_allow_html=True
    #         )
            
    #         # Display a progress bar
    #         progress = int((data['attempted'] / data['total_questions']) * 100) if data['total_questions'] else 0
    #         st.progress(progress / 100)
            
    #         # Resume button: disabled if the assignment is completed
    #         if st.button("▶ Resume", key=f"resume_{idx}", help="Continue where you left off", disabled=is_completed):
    #             assignment_id = resume_assignment(student_id, data["topic"], data["sub_topic"])
    #             if assignment_id:
    #                 st.session_state["student_id"] = student_id
    #                 st.session_state["current_assignment"] = assignment_id
    #                 st.session_state["current_question_index"] = 0
    #                 st.session_state["current_topic"] = data["topic"]
    #                 st.session_state["current_subtopic"] = data["sub_topic"]
    #                 st.switch_page("pages/question_page.py")
                    
    #         # Review button: only shown if at least one question is attempted
    #         if data['attempted'] > 0:
    #             if st.button("Review", key=f"review_{idx}", help="Review attempted questions"):
    #                 assignment_id = data["assignment_id"]
    #                 st.session_state["student_id"] = student_id
    #                 st.session_state["current_assignment"] = assignment_id
    #                 st.switch_page("pages/review_page.py")
                    
    #         st.markdown('</div>', unsafe_allow_html=True)
    
    # for idx, data in enumerate(progress_data):
    #     with st.container():
    #         st.markdown('<div class="card">', unsafe_allow_html=True)
            
    #         col1, col2 = st.columns([0.7, 0.3])
    #         with col1:
    #             st.markdown(f"<h4 style='color:#2E3A87; font-weight:bold;'>{data['topic']}</h4>", unsafe_allow_html=True)
    #             st.markdown(f"<h5 style='color:#4A5EA8; font-weight:semi-bold;'>{data['sub_topic']}</h5>", unsafe_allow_html=True)
    #             st.markdown(
    #                 f"<p style='font-size:16px; white-space: nowrap;'><b>Total Questions:</b> {data['total_questions']} &nbsp;&nbsp;|&nbsp;&nbsp; "
    #                 f"<b>Attempted:</b> {data['attempted']} &nbsp;&nbsp;|&nbsp;&nbsp; "
    #                 f"<b>Correct:</b> {data['correct']} &nbsp;&nbsp;|&nbsp;&nbsp; "
    #                 f"<b>Deadline:</b> {data['deadline']}</p>", 
    #                 unsafe_allow_html=True
    #             )

    #             # Progress Bar
    #             progress = int((data['attempted'] / data['total_questions']) * 100) if data['total_questions'] else 0
    #             st.progress(progress / 100)
            
    #     with col2:
    #                 # Check if assignment is completed
    #                 is_completed = data['total_questions'] == data['attempted']
    #                 button_text = "✔ Completed" if is_completed else "▶ Resume"
                    
    #                 # Button will be disabled if completed
    #                 if st.button(button_text, key=f"resume_{idx}", help="Continue where you left off", disabled=is_completed):
    #                     st.write("Debug: Starting Resume process")
    #                     st.write(f"Debug: Student ID - {student_id}")
    #                     st.write(f"Debug: Topic - {data['topic']}")
    #                     st.write(f"Debug: Sub Topic - {data['sub_topic']}")
                        
    #                     assignment_id = resume_assignment(student_id, data["topic"], data["sub_topic"])
    #                     st.write(f"Debug: Assignment ID returned - {assignment_id}")
                        
    #                     if assignment_id:
    #                         st.session_state["student_id"] = student_id
    #                         st.session_state["current_assignment"] = assignment_id
    #                         st.session_state["current_question_index"] = 0
    #                         st.session_state["current_topic"] = data["topic"]
    #                         st.session_state["current_subtopic"] = data["sub_topic"]
                            
    #                         st.write("Debug: All session states set, preparing to switch page")
    #                         st.switch_page("pages/question_page.py")


    #                 # Now add the Review button if at least one question is attempted
    #                 if data['attempted'] > 0:
    #                     if st.button("Review", key=f"review_{idx}", help="Review attempted questions"):
    #                         assignment_id = data["assignment_id"]  # or however you're storing it
    #                         st.session_state["student_id"] = student_id
    #                         st.session_state["current_assignment"] = assignment_id
    #                         st.switch_page("pages/review_page.py")

    #                 st.markdown('</div>', unsafe_allow_html=True)
else:
    st.info("No active assignments available.")