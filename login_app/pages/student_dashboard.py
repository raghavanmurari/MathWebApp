import streamlit as st
from database.db_connection import get_assignment_collection, get_user_collection, get_db
from bson.objectid import ObjectId
from services.question_service import get_current_question, update_student_response

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

student_id = str(user["_id"])

# Database connections
assignments_collection = get_assignment_collection()
db = get_db()
topics_collection = db["topics"]
responses_collection = db["responses"]

# Fetch student details
student_name = user.get("name", "Student")

# Custom CSS for larger font sizes
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
    </style>
""", unsafe_allow_html=True)

st.title(f"Welcome, {student_name}! 👋")

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
                # Extract text and clean up LaTeX format
                display_text = option.get('text', '')
                # Remove \( and \) and replace with proper LaTeX format
                display_text = display_text.replace('\\(', '').replace('\\)', '')
                display_values.append(display_text)
                option_mapping[display_text] = option

            # Create radio buttons with cleaned display values
            selected = st.radio(
                "Select your answer:",
                options=display_values,
                label_visibility="visible",
                format_func=lambda x: f"${x}$"
            )

            # Create columns for buttons
            col1, col2, col3 = st.columns([1, 0.2, 1])
            with col1:
                if st.button("Submit Answer", use_container_width=True):
                    if selected:
                        selected_option = option_mapping[selected]
                        update_student_response(
                            assignment_id=st.session_state["current_assignment"],
                            student_id=student_id,
                            question_id=current_question["_id"],
                            selected_answer=selected_option
                        )
                        st.rerun()
                    else:
                        st.warning("Please select an answer first.")
            with col3:
                if st.button("Back to Dashboard", use_container_width=True):
                    del st.session_state["current_assignment"]
                    if "current_question_index" in st.session_state:
                        del st.session_state["current_question_index"]
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
            # Fetch topic name properly
            topic = topics_collection.find_one({"_id": ObjectId(assignment.get("topic_id"))})
            assignment_name = topic.get("name", "Untitled Assignment") if topic else "Untitled Assignment"

            # Fetch attempted questions count
            attempted_questions = responses_collection.count_documents({
                "assignment_id": assignment["_id"],
                "student_id": ObjectId(student_id)
            })
            
            total_questions = len(assignment.get("sub_topics", []))
            progress_percent = (attempted_questions / total_questions) * 100 if total_questions else 0
            progress_text = f"{int(progress_percent)}% Complete"

            # Display assignment with progress
            col1, col2 = st.columns([0.7, 0.3])
            with col1:
                st.write(f"📖 **{assignment_name}**")
                st.progress(progress_percent / 100)
                st.caption(progress_text)

            with col2:
                button_label = "Resume" if attempted_questions > 0 else "Start"
                if st.button(button_label, key=str(assignment["_id"])):
                    st.session_state["current_assignment"] = str(assignment["_id"])
                    st.rerun()