# question_page.py
import streamlit as st
from database.db_connection import get_db, get_question_collection
from services.question_service import get_current_question, update_student_response
from utils.session_manager import clear_session

# Authentication checks
if "logged_in" not in st.session_state or not st.session_state.logged_in:
   st.warning("You must be logged in to access this page.")
   st.switch_page("pages/login_page.py")

if st.session_state.get("user_role") != "student":
   st.error("Unauthorized Access! Redirecting...")
   st.switch_page("pages/login_page.py")

# Verify current assignment exists
if "current_assignment" not in st.session_state:
   st.error("No active assignment selected.")
   st.switch_page("pages/student_dashboard.py")

# UI Styling
st.markdown("""
   <style>
   .large-text { font-size: 24px !important; margin-bottom: 20px; }
   .question-text { font-size: 20px !important; margin-bottom: 15px; }
   .stRadio [role=radiogroup] label { font-size: 18px !important; margin: 10px 0; }
   </style>
""", unsafe_allow_html=True)

# Display Question
current_question = get_current_question()
if current_question:
   st.markdown('<p class="large-text">Question</p>', unsafe_allow_html=True)
   st.markdown(f'<p class="question-text">{current_question["description"]}</p>', unsafe_allow_html=True)
   
   options = current_question.get("options", [])
   if options:
       display_values = []
       option_mapping = {}

       for option in options:
           display_text = option.get('text', '').replace('\\(', '').replace('\\)', '')
           display_values.append(display_text)
           option_mapping[display_text] = option

       selected = st.radio(
           "Select your answer:",
           options=display_values,
           label_visibility="visible",
           key="selected_option"
       )

       col1, col2 = st.columns([1, 1])
       with col1:
           if st.button("Submit Answer", use_container_width=True):
               if selected:
                   selected_option = option_mapping[selected]
                   is_correct = selected_option.get("is_correct", False)
                   
                   update_student_response(
                       assignment_id=st.session_state["current_assignment"],
                       student_id=st.session_state.get("student_id"),
                       question_id=current_question["_id"],
                       selected_answer=selected_option
                   )

                   if is_correct:
                       st.success("✅ Correct!")
                   else:
                       st.error("❌ Incorrect!")
                       correct_answer = next((opt["text"] for opt in options if opt["is_correct"]), "N/A")
                       st.info(f"The correct answer is: {correct_answer}")
                   
                   st.session_state["next_question_ready"] = True
                   # Display solution if available
                   if "solution" in current_question:
                       st.markdown("### Solution")
                       st.markdown(current_question["solution"])
                   elif "explanation" in current_question:
                       st.markdown("### Explanation")
                       st.markdown(current_question["explanation"])
       with col2:
           if st.button("Back to Dashboard", use_container_width=True):
               del st.session_state["current_assignment"]
               if "current_question_index" in st.session_state:
                   del st.session_state["current_question_index"]
               st.switch_page("pages/student_dashboard.py")

       if st.session_state.get("next_question_ready", False):
           if st.button("Next Question"):
               st.session_state["current_question_index"] += 1
               st.session_state["next_question_ready"] = False
               st.rerun()