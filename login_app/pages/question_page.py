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
        
        return attempted_count + 1
    except Exception as e:
        print(f"Error getting attempted count: {str(e)}")
        return 1

if "current_question_index" not in st.session_state:
    st.session_state.current_question_index = 0


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
        
        if not assignment_id or not student_id:
            print("Missing assignment_id or student_id")
            return False
        
        # Convert string IDs to ObjectId if needed
        assignment_obj_id = ObjectId(assignment_id) if isinstance(assignment_id, str) else assignment_id
        student_obj_id = ObjectId(student_id) if isinstance(student_id, str) else student_id
        
        # Get assignment details
        assignments = db["assignments"]
        assignment = assignments.find_one({"_id": assignment_obj_id})
        
        if not assignment:
            print(f"No assignment found with ID: {assignment_id}")
            return False
            
        # Get topic details
        topics = db["topics"]
        topic_data = topics.find_one({"_id": assignment["topic_id"]})
        
        # Get subtopic - assuming the first one if multiple exist
        sub_topics = assignment.get("sub_topics", [])
        if not sub_topics:
            print("No sub_topics found in assignment")
            return False
            
        sub_topic = sub_topics[0]
        
        if not topic_data:
            print(f"No topic found with ID: {assignment['topic_id']}")
            return False
            
        # Find all questions for this topic/subtopic
        questions = db["questions"]
        topic_questions_cursor = questions.find({
            "topic": topic_data["name"],
            "sub_topic": sub_topic
        })
        
        # Convert cursor to list and get IDs
        question_list = list(topic_questions_cursor)
        if not question_list:
            print(f"No questions found for topic '{topic_data['name']}' and sub_topic '{sub_topic}'")
            return False
            
        question_ids = [q["_id"] for q in question_list]
        
        # Get all responses for this student and assignment
        responses = db["responses"]
        attempted_questions = responses.distinct(
            "question_id",
            {
                "assignment_id": assignment_obj_id,
                "student_id": student_obj_id
            }
        )
        
        # Convert ObjectId to string for comparison if needed
        attempted_str = [str(q_id) for q_id in attempted_questions]
        question_str = [str(q_id) for q_id in question_ids]
        
        # Check if all questions are attempted
        all_attempted = all(q_id in attempted_questions for q_id in question_ids)
        
        if not all_attempted:
            # For debugging: which questions are missing
            missing = [str(q_id) for q_id in question_ids if q_id not in attempted_questions]
            print(f"Missing responses for questions: {missing}")
        
        return all_attempted
        
    except Exception as e:
        print(f"Error checking completion: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

# Initialize session states
if "submitted_answer" not in st.session_state:
    st.session_state.submitted_answer = False
if "question_answered" not in st.session_state:
    st.session_state.question_answered = False

# UI Styling
st.markdown("""
    <style>
    .large-text { font-size: 24px !important; margin-bottom: 20px; }
    .stMarkdown { font-size: 20px !important; margin-bottom: 15px; }
    .stRadio [role=radiogroup] {
        padding: 20px;  /* increased from 10px to 20px */
        background-color: #f0f2f6;
        border-radius: 10px;
        font-size: 18px !important;
        margin: 10px 0;
        gap: 15px;  /* This adds space between radio items */
        display: flex;
        flex-direction: column;
    }
    .stButton button {
        width: 100%;
    }
    
    /* Style for highlighted option */
    .selected-option {
        background-color: #ffedea; 
        padding: 8px;
        border-radius: 5px;
        border-left: 4px solid #FF4B4B;
        margin: 5px 0;
    }
    </style>
""", unsafe_allow_html=True)

# Single line header with center alignment
topic = st.session_state.get('current_topic', 'N/A')
subtopic = st.session_state.get('current_subtopic', 'N/A')
st.markdown(f"<h4 style='text-align: center;'>{topic} - {subtopic}</h4>", unsafe_allow_html=True)

# Get current question number and total
total_questions = get_total_questions()
current_question_num = get_attempted_count()

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
            st.markdown(
                f"**Difficulty:** <span style='color: {difficulty_color}'>{difficulty}</span>", 
                unsafe_allow_html=True
            )

    # Question display
    st.markdown("### Question")
    question_text = convert_latex(current_question["description"])
    st.markdown(question_text)  # Removed extra spacing
    
    options = current_question.get("options", [])
    if options:
        display_values = []
        option_mapping = {}
        original_texts = {}  # Store original text without ✅/❌

        # Create unique key for this question
        question_key = f"selected_option_{str(current_question['_id'])}"

        # Find the selected option text if already submitted
        selected_original_text = None
        if st.session_state.submitted_answer and "last_selected_option" in st.session_state:
            for option in options:
                if option == st.session_state.last_selected_option:
                    selected_original_text = convert_latex(option.get('text', ''))
                    break
        
        # If user has submitted, show the ✅ or ❌ next to the options
        for option in options:
            display_text = convert_latex(option.get('text', ''))
            original_texts[display_text] = display_text  # Store original text
            
            # Add highlighting prefix for the selected option
            if st.session_state.submitted_answer and selected_original_text == display_text:
                # Mark this option as highlighted
                if option.get("is_correct"):
                    display_text += " ✅"
                else:
                    display_text += " ❌"
            elif st.session_state.submitted_answer:
                # For other options just add checkmark if correct
                if option.get("is_correct"):
                    display_text += " ✅"
            
            display_values.append(display_text)
            option_mapping[display_text] = option

        # Display the radio options
        selected = st.radio(
            "",  # "Choose your answer:"
            options=display_values,
            label_visibility="visible",
            key=question_key,
            index=None,
            disabled=st.session_state.submitted_answer  # Disable after submission
        )
        
        # Display the highlighted option separately after submission
        if st.session_state.submitted_answer and selected_original_text:
            # Get the selected text with any checkmarks
            selected_display = None
            for display_text in display_values:
                if display_text.startswith(selected_original_text):
                    selected_display = display_text
                    break
                    
            if selected_display:
                st.markdown(f"""
                <div class="selected-option">
                <strong>Your answer:</strong> {selected_display}
                </div>
                """, unsafe_allow_html=True)

        col1, col2, col3 = st.columns([1, 1, 1])
        
        # 1) Submit: Mark the question as answered and trigger a refresh
        with col1:
            if st.button("Submit", use_container_width=True, disabled=st.session_state.question_answered):
                if selected:
                    st.session_state.question_answered = True
                    st.session_state.submitted_answer = True
                    
                    # Save the chosen option so we can store it on "Next"
                    selected_option = option_mapping[selected]
                    st.session_state.last_selected_option = selected_option
                    
                    # Immediately re-run so that the UI updates with checkmarks
                    st.rerun()

        # 2) Next: store answer in DB, load next question
        with col2:
            if st.button("Next", use_container_width=True, disabled=not st.session_state.question_answered):
                if "last_selected_option" in st.session_state:
                    update_student_response(
                        assignment_id=st.session_state["current_assignment"],
                        student_id=st.session_state.get("student_id"),
                        question_id=current_question["_id"],
                        selected_answer=st.session_state.last_selected_option
                    )
                    del st.session_state.last_selected_option

                st.session_state.current_question_index += 1
                st.session_state.question_answered = False
                st.session_state.submitted_answer = False
                
                # Clear the chosen option
                if question_key in st.session_state:
                    del st.session_state[question_key]
                
                st.rerun()

        with col3:
            if st.button("Back to Dashboard", use_container_width=True):
                del st.session_state["current_assignment"]
                if "current_question_index" in st.session_state:
                    del st.session_state["current_question_index"]
                if "progress_data" in st.session_state:
                    del st.session_state["progress_data"]
                st.switch_page("pages/student_dashboard.py")

        # If the user has submitted an answer, show solution/explanation now
        if st.session_state.submitted_answer:
            if check_subtopic_completion():
                st.success("🎉 Congratulations! You have completed all questions in this sub-topic!")

            # Show solution or explanation
            if "solution" in current_question:
                st.markdown("### Solution")
                solution_text = convert_latex(current_question["solution"])
                st.markdown(solution_text)
            elif "explanation" in current_question:
                st.markdown("### Explanation")
                explanation_text = convert_latex(current_question["explanation"])
                st.markdown(explanation_text)