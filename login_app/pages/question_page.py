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

# Get total questions for the current assignment
def get_total_questions():
    try:
        db = get_db()
        assignment = db["assignments"].find_one({"_id": ObjectId(st.session_state["current_assignment"])})
        if assignment:
            topic = db["topics"].find_one({"_id": assignment["topic_id"]})
            if topic and assignment.get("sub_topics"):
                return db["questions"].count_documents({
                    "topic": topic["name"],
                    "sub_topic": {"$in": assignment["sub_topics"]}
                })
    except Exception as e:
        print(f"Error getting total questions: {str(e)}")
    return 0

def get_attempted_count():
    try:
        db = get_db()
        assignment_id = st.session_state["current_assignment"]
        student_id = st.session_state.get("student_id")
        
        responses = db["responses"]
        attempted_count = responses.count_documents({
            "assignment_id": ObjectId(assignment_id),
            "student_id": ObjectId(student_id)
        })
        
        return attempted_count + 1  # Add 1 for the current question
    except Exception as e:
        print(f"Error getting attempted count: {str(e)}")
        return 1

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
        
        assignments = db["assignments"]
        assignment = assignments.find_one({"_id": ObjectId(assignment_id)})
        
        if not assignment:
            return False
            
        questions = db["questions"]
        responses = db["responses"]
        
        topics = db["topics"]
        topic_data = topics.find_one({"_id": assignment["topic_id"]})
        sub_topic = assignment.get("sub_topics", [])[0] if assignment.get("sub_topics") else None
        
        if not topic_data or not sub_topic:
            return False
            
        topic_questions = questions.find({
            "topic": topic_data["name"],
            "sub_topic": sub_topic
        })
        question_ids = [q["_id"] for q in topic_questions]
        
        attempted_questions = responses.distinct(
            "question_id",
            {
                "assignment_id": ObjectId(assignment_id),
                "student_id": ObjectId(student_id)
            }
        )
        
        return all(q_id in attempted_questions for q_id in question_ids)
        
    except Exception as e:
        print(f"Error checking completion: {str(e)}")
        return False

# UI Styling
st.markdown("""
    <style>
    .large-text { font-size: 24px !important; margin-bottom: 20px; }
    .stMarkdown { font-size: 20px !important; margin-bottom: 15px; }
    .stRadio [role=radiogroup] {
        padding: 10px;
        background-color: #f0f2f6;
        border-radius: 10px;
        font-size: 18px !important;
        margin: 10px 0;
    }
    .stButton button {
        width: 100%;
    }
    </style>
""", unsafe_allow_html=True)

# Single line header with center alignment
topic = st.session_state.get('current_topic', 'N/A')
subtopic = st.session_state.get('current_subtopic', 'N/A')
st.markdown(f"<h4 style='text-align: center;'>{topic} - {subtopic}</h4>", unsafe_allow_html=True)

# Get current question number and total
total_questions = get_total_questions()
current_question_num = get_attempted_count()  # Changed this line to use the new function

# Initialize answered state if not exists
if "question_answered" not in st.session_state:
    st.session_state.question_answered = False

# Display Question
current_question = get_current_question()
if current_question:
    # Progress bar
    progress = current_question_num / total_questions
    st.progress(progress)

    # Question counter and difficulty display
    col1, col2 = st.columns([1, 1])
    with col1:
        st.markdown(f"**Question {current_question_num} of {total_questions}**")
    with col2:
        if "difficulty" in current_question:
            difficulty = current_question.get("difficulty", "Medium")
            difficulty_color = {
                "Easy": "green",
                "Medium": "orange",
                "Hard": "red"
            }.get(difficulty, "blue")
            st.markdown(f"**Difficulty:** <span style='color: {difficulty_color}'>{difficulty}</span>", 
                       unsafe_allow_html=True)

    # Question display with original LaTeX handling
    st.markdown("## Question")
    question_text = convert_latex(current_question["description"])
    st.markdown(question_text)
    
    options = current_question.get("options", [])
    if options:
        display_values = []
        option_mapping = {}

        for option in options:
            display_text = convert_latex(option.get('text', ''))
            display_values.append(display_text)
            option_mapping[display_text] = option

        selected = st.radio(
            "Choose your answer:",
            options=display_values,
            label_visibility="visible",
            key="selected_option",
            index=None
        )

        # Button layout
        col1, col2, col3 = st.columns([1, 1, 1])
        
        with col1:
            if st.button("Submit", use_container_width=True, disabled=st.session_state.question_answered):
                if selected:
                    st.session_state.question_answered = True
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
                        correct_answer = convert_latex(correct_answer)
                        st.markdown(f"The correct answer is: {correct_answer}")
                    
                    if check_subtopic_completion():
                        st.success("🎉 Congratulations! You have completed all questions in this sub-topic!")
                    
                    # Display solution/explanation
                    if "solution" in current_question:
                        st.markdown("### Solution")
                        solution_text = convert_latex(current_question["solution"])
                        st.markdown(solution_text)
                    elif "explanation" in current_question:
                        st.markdown("### Explanation")
                        explanation_text = convert_latex(current_question["explanation"])
                        st.markdown(explanation_text)
        
        with col2:
            if st.button("Next", use_container_width=True, disabled=not st.session_state.question_answered):
                st.session_state.current_question_index += 1
                st.session_state.question_answered = False
                st.rerun()
        
        with col3:
            if st.button("Back to Dashboard", use_container_width=True):
                del st.session_state["current_assignment"]
                if "current_question_index" in st.session_state:
                    del st.session_state["current_question_index"]
                if "progress_data" in st.session_state:
                    del st.session_state["progress_data"]
                st.switch_page("pages/student_dashboard.py")