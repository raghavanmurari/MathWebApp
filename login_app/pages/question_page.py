import streamlit as st
from database.db_connection import get_db, get_question_collection
from services.question_service import get_current_question, update_student_response
from utils.session_manager import clear_session
from bson.objectid import ObjectId

# Authentication checks
if "logged_in" not in st.session_state or not st.session_state.logged_in:
   st.warning("You must be logged in to access this page.")
   st.switch_page("pages/login_page.py")

if st.session_state.get("user_role") != "student":
   st.error("Unauthorized Access! Redirecting...")
   st.switch_page("pages/login_page.py")

# Single line header with center alignment
topic = st.session_state.get('current_topic', 'N/A')
subtopic = st.session_state.get('current_subtopic', 'N/A')
st.markdown(f"<h4 style='text-align: center;'>{topic} - {subtopic}</h4>", unsafe_allow_html=True)

# Verify current assignment exists
if "current_assignment" not in st.session_state:
   st.error("No active assignment selected.")
   st.switch_page("pages/student_dashboard.py")

def convert_latex(text):
    """Convert Excel LaTeX format to Streamlit-compatible format"""
    if text and isinstance(text, str):
        return text.replace('\\(', '$').replace('\\)', '$')
    return text

def check_subtopic_completion():
    """Check if all questions in the current sub-topic have been attempted"""
    try:
        db = get_db()
        assignment_id = st.session_state["current_assignment"]
        student_id = st.session_state.get("student_id")
        
        # Get assignment details to find topic and sub-topic
        assignments = db["assignments"]
        assignment = assignments.find_one({"_id": ObjectId(assignment_id)})
        
        if not assignment:
            return False
            
        # Get questions for this sub-topic
        questions = db["questions"]
        responses = db["responses"]
        
        # Get topic and sub-topic from assignment
        topics = db["topics"]
        topic_data = topics.find_one({"_id": assignment["topic_id"]})
        sub_topic = assignment.get("sub_topics", [])[0] if assignment.get("sub_topics") else None
        
        if not topic_data or not sub_topic:
            return False
            
        # Get all questions for this topic and sub-topic
        topic_questions = questions.find({
            "topic": topic_data["name"],
            "sub_topic": sub_topic
        })
        question_ids = [q["_id"] for q in topic_questions]
        
        # Get all attempted questions
        attempted_questions = responses.distinct(
            "question_id",
            {
                "assignment_id": ObjectId(assignment_id),
                "student_id": ObjectId(student_id)
            }
        )
        
        # Check if all questions have been attempted
        return all(q_id in attempted_questions for q_id in question_ids)
        
    except Exception as e:
        print(f"Error checking completion: {str(e)}")
        return False

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
#    st.markdown('<p class="large-text">Question</p>', unsafe_allow_html=True)
    # Modified code that will fix LaTeX rendering:
   st.markdown("## Question")  # Using markdown header instead of HTML
   question_text = convert_latex(current_question["description"])
   st.markdown(question_text)  # Remove HTML wrapping to allow LaTeX to render
   
   # The styling can be moved to the CSS section:
   st.markdown("""
        <style>
        .large-text { font-size: 24px !important; margin-bottom: 20px; }
        /* Remove question-text class since we're using native markdown */
        .stMarkdown { font-size: 20px !important; margin-bottom: 15px; }
        .stRadio [role=radiogroup] label { font-size: 18px !important; margin: 10px 0; }
        </style>
    """, unsafe_allow_html=True)

   options = current_question.get("options", [])
   if options:
       display_values = []
       option_mapping = {}

       for option in options:
           # Convert LaTeX in option text
           display_text = convert_latex(option.get('text', ''))
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
                       # Convert LaTeX in correct answer
                       correct_answer = convert_latex(correct_answer)
                       st.info(f"The correct answer is: {correct_answer}")
                   
                   # Check if this was the last question in the sub-topic
                   if check_subtopic_completion():
                       st.success("🎉 Congratulations! You have completed all questions in this sub-topic!")
                       if st.button("Return to Dashboard"):
                           del st.session_state["current_assignment"]
                           if "current_question_index" in st.session_state:
                               del st.session_state["current_question_index"]
                           if "progress_data" in st.session_state:
                               del st.session_state["progress_data"]
                           st.switch_page("pages/student_dashboard.py")
                   else:
                       st.session_state["next_question_ready"] = True
                   
                   # Display solution if available
                   if "solution" in current_question:
                       st.markdown("### Solution")
                       # Convert LaTeX in solution
                       solution_text = convert_latex(current_question["solution"])
                       st.markdown(solution_text)
                   elif "explanation" in current_question:
                       st.markdown("### Explanation")
                       # Convert LaTeX in explanation
                       explanation_text = convert_latex(current_question["explanation"])
                       st.markdown(explanation_text)
       with col2:
           if st.button("Back to Dashboard", use_container_width=True):
               del st.session_state["current_assignment"]
               if "current_question_index" in st.session_state:
                   del st.session_state["current_question_index"]
               if "progress_data" in st.session_state:
                   del st.session_state["progress_data"]
               st.switch_page("pages/student_dashboard.py")

       if st.session_state.get("next_question_ready", False):
           if st.button("Next Question"):
               st.session_state["current_question_index"] += 1
               st.session_state["next_question_ready"] = False
               st.rerun()