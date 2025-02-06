import streamlit as st
from database.db_connection import get_assignment_collection, get_user_collection, get_db
from bson.objectid import ObjectId
from services.question_service import get_current_question, update_student_response
from utils.session_manager import clear_session

# Ensure only students can access this page
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

# Database connections
assignments_collection = get_assignment_collection()
db = get_db()
topics_collection = db["topics"]
responses_collection = db["responses"]

# Fetch student details
student_name = user.get("name", "Student")

# Updated the CSS to include the feedback styling
st.markdown("""
    <style>
    .large-text {
        font-size: 24px !important;
        margin-bottom: 20px;
    }
    .question-text {
        font-size: 20px !important;
        margin-bottom: 15px;
    }
    .stRadio [role=radiogroup] label {
        font-size: 18px !important;
        margin: 10px 0;
    }
    .block-container {padding-top: 2rem; max-width: 1200px;}
    /* Feedback icons styling */
    .option-feedback {
        display: inline-flex;
        align-items: center;
        margin-left: 10px;
    }
    .stRadio [role=radiogroup] {
        position: relative;
    }
    </style>
""", unsafe_allow_html=True)

col1, col2 = st.columns([0.5, 0.1])

with col1:
    st.title(f"Welcome, {student_name}! 👋")
with col2:
    if st.button("Logout", help="Click to logout"):
        clear_session()
        st.switch_page("pages/login_page.py")

# Check if we're in question mode
if "current_assignment" in st.session_state:
    current_question = get_current_question()
    if current_question:
        st.markdown('<p class="large-text">Question</p>', unsafe_allow_html=True)
        st.markdown(f'<p class="question-text">{current_question["description"]}</p>', unsafe_allow_html=True)
        st.markdown('<p class="question-text">Select your answer:</p>', unsafe_allow_html=True)

        # Display options if available
        options = current_question.get("options", [])
        if options:
            # Create lists for storing clean display values and mapping
            display_values = []
            option_mapping = {}

            # Process each option for clean display
            for option in options:
                display_text = option.get('text', '')
                display_text = display_text.replace('\\(', '').replace('\\)', '')
                display_values.append(display_text)
                option_mapping[display_text] = option

            # Initialize session states if not already present
            if "selected_option" not in st.session_state:
                st.session_state.selected_option = None
            if "is_correct" not in st.session_state:
                st.session_state.is_correct = None
            if "submitted" not in st.session_state:
                st.session_state.submitted = False

            def handle_option_selection():
                if st.session_state.selected_option:
                    selected_option = option_mapping[st.session_state.selected_option]
                    st.session_state.is_correct = selected_option.get("is_correct", False)
                    # Reset submitted state when new option is selected
                    st.session_state.submitted = False

            selected = st.radio(
                "Select your answer:",
                options=display_values,
                label_visibility="visible",
                format_func=lambda x: (f"${x}$ "),
                key="selected_option",
                on_change=handle_option_selection
            )

            # Create button layout
            col1, col2, col3 = st.columns([1, 0.2, 1])
            with col1:
                submit_clicked = st.button("Submit Answer", use_container_width=True)
            with col3:
                if st.button("Back to Dashboard", use_container_width=True):
                    del st.session_state["current_assignment"]
                    if "current_question_index" in st.session_state:
                        del st.session_state["current_question_index"]
                    st.rerun()

            # If submit button is clicked
            if submit_clicked:
                if selected:
                    selected_option = option_mapping[selected]
                    
                    # Determine correctness
                    is_correct = selected_option.get("is_correct", False)
                    st.session_state["last_submission_correct"] = is_correct
                    st.session_state.submitted = True

                    # Save response to database
                    update_student_response(
                        assignment_id=st.session_state["current_assignment"],
                        student_id=student_id,
                        question_id=current_question["_id"],
                        selected_answer=selected_option
                    )

                    # Find the correct answer
                    correct_answer = next((opt["text"] for opt in options if opt["is_correct"]), "N/A")

                    # Feedback section
                    st.markdown("### Feedback:")

                    # Show feedback next to selected option with LaTeX rendering
                    if is_correct:
                        st.success(f"✅ Correct!")
                    else:
                        st.markdown(
                            f'<div style="background-color: #F8D7DA; padding: 10px; border-radius: 5px; color: #721C24;">'
                            f'❌ Incorrect!'
                            f'</div>', unsafe_allow_html=True
                        )
                        st.markdown(
                            f'<div style="background-color: #D1ECF1; padding: 10px; border-radius: 5px; color: #0C5460;">'
                            f'✅ The correct answer is: $$ {correct_answer} $$.'
                            f'</div>', unsafe_allow_html=True
                        )

                    # Display solution immediately after feedback
                    if "solution" in current_question:
                        st.markdown("### Solution:")
                        st.markdown(current_question["solution"])


                    # Enable "Next Question" button
                    st.session_state["next_question_ready"] = True


                    # Enable "Next Question" button after submission
                    st.session_state["next_question_ready"] = True
                    #st.rerun()

            # Display "Next Question" button only if an answer was submitted
            if st.session_state.get("next_question_ready", False):
                if st.button("Next Question"):
                    st.session_state["current_question_index"] += 1
                    st.session_state["next_question_ready"] = False
                    # Reset submitted state for next question
                    st.session_state.submitted = False
                    st.rerun()

else:
    # Show assignments list
    st.subheader("Your Active Assignments")

    # Fetch active assignments assigned to this student
    active_assignments = list(assignments_collection.find(
        {"students": ObjectId(student_id), "status": "active"}
    ))

    if not active_assignments:
        st.info("No active assignments available.")
    else:
        for assignment in active_assignments:
            topic = topics_collection.find_one({"_id": ObjectId(assignment.get("topic_id"))})
            assignment_name = topic.get("name", "Untitled Assignment") if topic else "Untitled Assignment"

            attempted_questions = responses_collection.count_documents({
                "assignment_id": assignment["_id"],
                "student_id": ObjectId(student_id)
            })
            
            total_questions = len(assignment.get("sub_topics", []))
            progress_percent = (attempted_questions / total_questions) * 100 if total_questions else 0
            progress_text = f"{int(progress_percent)}% Complete"

            col1, col2 = st.columns([0.7, 0.3])
            with col1:
                st.write(f"📖 **{assignment_name}**")
                st.progress(min(progress_percent / 100, 1.0))  
                st.write(f"Debug: Progress Percent = {progress_percent}")
                st.caption(progress_text)

            with col2:
                button_label = "Resume" if attempted_questions > 0 else "Start"
                if st.button(button_label, key=str(assignment["_id"])):
                    st.session_state["current_assignment"] = str(assignment["_id"])
                    st.rerun()