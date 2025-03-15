import streamlit as st
from utils.session_manager import clear_session, load_session
from pages.student_list import display_students
# from pages.display_question_bank import display_question_bank, get_db  
from database.db_connection import get_user_collection, get_assignment_collection
from bson.objectid import ObjectId  
from pages.create_assignment import show_create_assignment
from utils.progress_tracking import ProgressTracker
import pandas as pd
from pages.display_question_bank import display_question_bank, view_questions, get_db


# from utils.pdf_generator import generate_pdf_report
from datetime import datetime

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_role = None
    st.session_state.user_email = None
    st.session_state.remember_me = False
    
# ✅ Remove Sidebar & Set Page Config
st.set_page_config(
    page_title="Teacher Dashboard",
    page_icon="🎓",
    layout="centered",
    initial_sidebar_state="collapsed"  # ✅ Hide sidebar
)

# ✅ Hide Sidebar Completely
st.markdown(
    """
    <style>
        [data-testid="stSidebar"] {display: none;}
        .block-container {padding-top: 2rem; max-width: 1200px;}
        .stTabs {margin-top: 1rem;}
        .stTabs [data-baseweb="tab-list"] {gap: 2rem;}
        .stTabs [data-baseweb="tab"] {height: 50px; padding: 0 20px; background-color: white; border-radius: 5px;}
        button[kind="secondary"] {
            margin-top: 3rem !important;
            position: relative;
            top: 20px;
        }
    </style>
    """,
    unsafe_allow_html=True
)

load_session()

if not st.session_state.logged_in:
    st.switch_page("pages/login_page.py")

# Add this after load_session()
def get_teacher_name():
    if "user_id" in st.session_state:
        users_collection = get_user_collection()
        teacher = users_collection.find_one({"_id": ObjectId(st.session_state["user_id"])})
        return teacher.get("name", "Teacher") if teacher else "Teacher"
    return "Teacher"

# Replace the title section with:
col1, col2 = st.columns([0.9, 0.1])
with col1:
    teacher_name = get_teacher_name()
    st.title(f"Welcome, {teacher_name} 👋")
with col2:
    if st.button("Logout", help="Click to logout"):
        clear_session()
        st.switch_page("pages/login_page.py")

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "🏠 Dashboard",
    "👩‍🏫 List of Students",
    "📚 Question Bank",
    "📝 Create Assignments",
    "📊 Generate Reports",
    "🔎 View Questions"  # New tab
])


# ✅ Fetch Total Students
users_collection = get_user_collection()
total_students = users_collection.count_documents({"role": "student"})

# ✅ Fetch Active Assignments
assignments_collection = get_assignment_collection()
active_assignments = assignments_collection.count_documents({"status": "active"})


def get_accuracy_color(accuracy):
    """Returns color-coded accuracy levels for easy interpretation."""
    if accuracy > 80:
        return "🟢 " + str(round(accuracy, 2)) + "%"
    elif accuracy >= 50:
        return "🟡 " + str(round(accuracy, 2)) + "%"
    else:
        return "🔴 " + str(round(accuracy, 2)) + "%"
    

with tab1:
    st.header("Welcome to the Teacher Dashboard")
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric(label="Total Students", value=total_students)
    with col2:
        st.metric(label="Active Assignments", value=active_assignments)

with tab2:
    st.header("Student Management")
    search_query = st.text_input("🔍 Search Students by Name or Email")
    display_students(search_query)

with tab3:
    display_question_bank()

# ✅ Fetch and Display Assignments With Assigned Students and Their User ID
with tab4:
    st.header("Assignments & Tests")
    st.subheader("Current Assignments")

    # Always show current assignments first
    assignments_collection = get_assignment_collection()
    db = get_db()
    topics_collection = db['topics']
    users_collection = db['users']
    students_collection = db['students']  # ✅ Fetch students collection

    if "user_id" not in st.session_state or st.session_state["user_id"] is None:
        st.warning("Session expired. Please log in again.")
        st.switch_page("pages/login_page.py")

    teacher_id = st.session_state["user_id"]
    
    try:
        teacher_object_id = ObjectId(teacher_id)
        assignments = list(assignments_collection.find({"teacher_id": teacher_object_id}))

        if assignments:
            assignment_data = []
            for assignment in assignments:
                topic_id = assignment.get("topic_id")
                topic_name = "Unknown Topic"
                if topic_id:
                    try:
                        topic_doc = topics_collection.find_one({"_id": ObjectId(str(topic_id))})
                        if topic_doc:
                            topic_name = topic_doc.get("name", "Unknown Topic")
                    except Exception as e:
                        st.warning(f"Error fetching topic name: {str(e)}")
                # Instead of joining them, just get the sub_topics list
                subtopics_list = assignment.get("sub_topics", ["No sub-topics"])
                created_str = assignment.get("created_at").strftime("%Y-%m-%d %H:%M") if assignment.get("created_at") else "No date"
                deadline_str = assignment.get("deadline").strftime("%Y-%m-%d %H:%M") if assignment.get("deadline") else "No deadline"

                deadline = assignment.get("deadline", "No deadline").strftime("%Y-%m-%d %H:%M") if assignment.get("deadline") else "No deadline"
                status = assignment.get("status", "Unknown")

                # ✅ Fetch Student Names and User IDs
                student_names = []
                student_user_ids = []
                student_grades = []  # NEW list for grades

                student_ids = assignment.get("students", [])
                if student_ids:
                    for student_id in student_ids:
                        try:
                            # Fetch student details from `students` collection
                            student_doc = students_collection.find_one({"_id": ObjectId(str(student_id))})
                            if student_doc:
                                # Get grade from student document as in student_list.py
                                grade = student_doc.get("grade", "N/A")
                                student_grades.append(str(grade))

                                user_id = student_doc.get("user_id")

                                # Fetch user details from `users` collection using user_id
                                user_doc = users_collection.find_one({"_id": ObjectId(str(user_id))})
                                if user_doc:
                                    student_names.append(user_doc.get("name", "Unknown Student"))
                                    student_user_ids.append(str(user_id))  # ✅ Display correct `user_id`
                                else:
                                    student_names.append("No student found")
                                    student_user_ids.append(str(user_id))
                                    student_grades.append("N/A")
                            else:
                                student_names.append("No student found")
                                student_user_ids.append("N/A")
                                student_grades.append("N/A")
                        except Exception as e:
                            student_names.append(f"Error: {str(e)}")
                            student_user_ids.append("N/A")
                            student_grades.append("N/A")

                assigned_students = ", ".join(student_names) if student_names else "No students assigned"
                assigned_student_ids = ", ".join(student_user_ids) if student_user_ids else "No students assigned"
                grade_str = ", ".join(student_grades) if student_grades else "N/A"

                assignment_data.append({
                    "Topic": topic_name,  # Add Topic as first column
                    "Sub-Topics": ", ".join(subtopics_list),
                    "Created": assignment.get("created_at").strftime("%Y-%m-%d %H:%M") if assignment.get("created_at") else "No date",
                    "Deadline": deadline,
                    "Status": status,
                    "Assigned Students": assigned_students,
                    "Grade": grade_str  
                    })

            if assignment_data:
                st.dataframe(
                    assignment_data,
                    use_container_width=True,
                    column_config={

                        "Sub-Topics": st.column_config.TextColumn("Sub-Topics"),
                        "Created": st.column_config.TextColumn("Created Date"),  # Add this line
                        "Deadline": st.column_config.TextColumn("Deadline"),
                        "Status": st.column_config.TextColumn("Status", width="small"),
                        "Assigned Students": st.column_config.TextColumn("Assigned Students"),
                        # "Student User IDs": st.column_config.TextColumn("Student User IDs")  # ✅ New Column
                        "Grade": st.column_config.TextColumn("Grade")
                    }
                )
            else:
                st.info("No assignments found.")
                
        else:
            st.info("No assignments found for this teacher.")
            
    except Exception as e:
        st.error(f"Error fetching assignments: {str(e)}")

    # Create New Assignment button below the table
    if st.button("Create New Assignment", type="primary"):
        st.session_state['show_create'] = True
        st.rerun()

    # Show create form if button was clicked
    if st.session_state.get('show_create', False):
        st.markdown("---")  # Add a separator
        show_create_assignment()



with tab5:
    # st.header("📊 Student Progress")
    st.header("")
    # Fetch required collections
    db = get_db()
    students_collection = db["students"]
    users_collection = db["users"]
    assignments_collection = db["assignments"]
    responses_collection = db["responses"]
    topics_collection = db["topics"]

    # Create students dictionary for dropdown
    students_dict = {}
    for student in students_collection.find({}):
        user_doc = users_collection.find_one({"_id": student["user_id"]})
        student_name = user_doc["name"] if user_doc and "name" in user_doc else "Unknown Student"
        students_dict[str(student["_id"])] = student_name

    if not students_dict:
        st.warning("No students found.")
    else:
        # Create two columns for filters
        col1, col2 = st.columns(2)
        
        with col1:
            student_id = st.selectbox(
                "Select a Student:", 
                options=list(students_dict.keys()), 
                format_func=lambda x: students_dict[x]
            )

        # Get all topics and subtopics from active assignments
        topic_subtopic_options = ["All Topics"]
        topic_subtopic_map = {}  # To store the mapping of display string to actual values
        
        if student_id:
            active_assignments = list(assignments_collection.find({
                "students": ObjectId(student_id),
                "status": "active"
            }))
            
            for assignment in active_assignments:
                topic_id = assignment.get("topic_id")
                if topic_id:
                    topic_doc = topics_collection.find_one({"_id": ObjectId(str(topic_id))})
                    if topic_doc:
                        topic_name = topic_doc.get("name")
                        for subtopic in assignment.get("sub_topics", []):
                            display_string = f"{topic_name} - {subtopic}"
                            topic_subtopic_options.append(display_string)
                            topic_subtopic_map[display_string] = {
                                'topic': topic_name,
                                'subtopic': subtopic
                            }
        with col2:
            if len(topic_subtopic_options) > 1:
                selected_topic_subtopics = st.multiselect(
                    "Select one or more Topic - Subtopic combinations:",
                    options=topic_subtopic_options,
                    default=["All Topics"]
                )
            else:
                st.warning("No topics found for this student.")
                selected_topic_subtopics = ["All Topics"]

        if student_id:
            student_name = students_dict[student_id]
            # st.subheader(f"Progress for {student_name}")

            if not active_assignments:
                st.warning("No active assignments for this student.")
            else:
                table_data = []
                total_practice_days = 0
                
                for assignment in active_assignments:
                    topic_id = assignment.get("topic_id")
                    topic_name = "Unknown Topic"
                    if topic_id:
                        topic_doc = topics_collection.find_one({"_id": ObjectId(str(topic_id))})
                        if topic_doc:
                            topic_name = topic_doc.get("name")

                    responses = list(responses_collection.find({
                        "student_id": ObjectId(student_id),
                        "assignment_id": assignment["_id"]
                    }))

                    questions_collection = db["questions"]
                    questions = {
                        str(q["_id"]): q for q in questions_collection.find({
                            "_id": {"$in": [r["question_id"] for r in responses]}
                        })
                    }

                    for sub_topic in assignment.get("sub_topics", []):
                        current_combo = f"{topic_name} - {sub_topic}"
                        if "All Topics" not in selected_topic_subtopics and current_combo not in selected_topic_subtopics:
                            continue

                        subtopic_responses = [r for r in responses 
                            if str(r["question_id"]) in questions 
                            and questions[str(r["question_id"])].get("sub_topic") == sub_topic]

                        easy_accuracy = 0
                        medium_accuracy = 0
                        hard_accuracy = 0

                        for difficulty in ["Easy", "Medium", "Hard"]:
                            difficulty_responses = [r for r in subtopic_responses 
                                if questions[str(r["question_id"])].get("difficulty") == difficulty]
                            correct = sum(1 for r in difficulty_responses if r.get("is_correct"))
                            total = len(difficulty_responses)
                            accuracy = (correct / total * 100) if total > 0 else 0
                            
                            if difficulty == "Easy":
                                easy_accuracy = accuracy
                            elif difficulty == "Medium":
                                medium_accuracy = accuracy
                            else:
                                hard_accuracy = accuracy

                        practice_dates = {r.get("timestamp").date() for r in subtopic_responses if r.get("timestamp")}
                        num_practice_days = len(practice_dates)
                        total_practice_days += num_practice_days

                        created_str = assignment.get("created_at").strftime("%Y-%m-%d") if assignment.get("created_at") else "No date"
                        deadline_str = assignment.get("deadline").strftime("%Y-%m-%d") if assignment.get("deadline") else "No deadline"

                        table_data.append([
                            topic_name,
                            sub_topic,
                            created_str,
                            deadline_str,
                            num_practice_days,
                            get_accuracy_color(easy_accuracy),
                            get_accuracy_color(medium_accuracy),
                            get_accuracy_color(hard_accuracy)
                        ])

                if table_data:
                    def extract_accuracy(accuracy_str):
                        # Remove emoji and % symbol, convert to float
                        return float(accuracy_str.split()[1].replace('%', ''))

                    avg_accuracies = {
                        "Easy": sum(extract_accuracy(row[5]) for row in table_data) / len(table_data),
                        "Medium": sum(extract_accuracy(row[6]) for row in table_data) / len(table_data),
                        "Hard": sum(extract_accuracy(row[7]) for row in table_data) / len(table_data)
                    }

                    # Determine focus area and strength
                    focus_needed_level = min(avg_accuracies, key=avg_accuracies.get)
                    strength_level = max(avg_accuracies, key=avg_accuracies.get)

                    # Get the current assignment IDs that the user has selected through the UI
                    selected_assignment_ids = []
                    if "All Topics" in selected_topic_subtopics:
                        # If "All Topics" is selected, include all active assignments
                        selected_assignment_ids = [assignment["_id"] for assignment in active_assignments]
                    else:
                        # Otherwise, only include assignments for the selected topics/subtopics
                        for assignment in active_assignments:
                            topic_id = assignment.get("topic_id")
                            if topic_id:
                                topic_doc = topics_collection.find_one({"_id": ObjectId(str(topic_id))})
                                if topic_doc:
                                    topic_name = topic_doc.get("name")
                                    for subtopic in assignment.get("sub_topics", []):
                                        display_string = f"{topic_name} - {subtopic}"
                                        if display_string in selected_topic_subtopics:
                                            selected_assignment_ids.append(assignment["_id"])
                                            break

                    # Calculate accuracy for just the selected assignments
                    total_correct = 0
                    total_questions = 0

                    # Query responses only for the selected assignments
                    filtered_responses = list(responses_collection.find({
                        "student_id": ObjectId(student_id),
                        "assignment_id": {"$in": selected_assignment_ids}
                    }))

                    for response in filtered_responses:
                        if response.get("is_correct"):
                            total_correct += 1
                        total_questions += 1

                    # Add debug text to verify the calculation
                    # st.text(f"Debug: {total_correct} correct out of {total_questions} questions")
                    # Calculate overall accuracies
                    # def extract_accuracy(accuracy_str):
                    #     # Remove emoji and % symbol, convert to float
                    #     return float(accuracy_str.split()[1].replace('%', ''))

                    # avg_accuracies = {
                    #     "Easy": sum(extract_accuracy(row[5]) for row in table_data) / len(table_data),
                    #     "Medium": sum(extract_accuracy(row[6]) for row in table_data) / len(table_data),
                    #     "Hard": sum(extract_accuracy(row[7]) for row in table_data) / len(table_data)
                    # }

                    # # Determine focus area and strength
                    # focus_needed_level = min(avg_accuracies, key=avg_accuracies.get)
                    # strength_level = max(avg_accuracies, key=avg_accuracies.get)

            
            # Add this CSS at the beginning of your script where other styles are defined
            st.markdown("""
                <style>
                    .metric-container {
                        background-color: #f8f9fa;
                        border-radius: 8px;
                        padding: 20px;
                        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
                    }
                    .stat-header {
                        color: #6b7280;
                        font-size: 14px;
                        font-weight: 600;
                        text-transform: uppercase;
                        letter-spacing: 0.05em;
                    }
                    .stat-value {
                        color: #111827;
                        font-size: 24px;
                        font-weight: 700;
                        margin-top: 4px;
                    }
                    .highlight {
                        background-color: #f3f4f6;
                        padding: 2px 6px;
                        border-radius: 4px;
                        font-weight: 500;
                    }
                    .stDataFrame {
                        padding: 1rem;
                        border-radius: 8px;
                        border: 1px solid #e5e7eb;
                    }
                </style>
            """, unsafe_allow_html=True)

            # Replace the existing report section with this:
            if st.button("Generate Report", key=f"progress_report_{student_id}"):
                # Create tabs for different sections of the report
                report_tabs = st.tabs(["Overview 📊", "Details 📝", "Recommendations 💡"])
                
                with report_tabs[0]:
                    # Header with student info
                    st.markdown(f"### Performance Report for {student_name}")
                    
                    # Key metrics in a 2x2 grid with custom styling
                    col1, col2 = st.columns(2)
                    with col1:
                        st.markdown("""
                            <div class="metric-container">
                                <div class="stat-header">Practice Engagement</div>
                                <div class="stat-value">📅 {total_practice_days} out of 7 Days</div>
                            </div>
                        """.format(total_practice_days=total_practice_days), unsafe_allow_html=True)
                        
                        st.markdown("""
                            <div class="metric-container" style="margin-top: 1rem;">
                                <div class="stat-header">Focus Area Needed</div>
                                <div class="stat-value">🎯 {level} ({accuracy:.1f}%)</div>
                            </div>
                        """.format(
                            level=focus_needed_level,
                            accuracy=avg_accuracies[focus_needed_level]
                        ), unsafe_allow_html=True)

                    with col2:
                        st.markdown("""
                            <div class="metric-container">
                                <div class="stat-header">Strongest Area</div>
                                <div class="stat-value">🏆 {level} ({accuracy:.1f}%)</div>
                            </div>
                        """.format(
                            level=strength_level,
                            accuracy=avg_accuracies[strength_level]
                        ), unsafe_allow_html=True)
                        
                        # overall_accuracy = sum(avg_accuracies.values()) / len(avg_accuracies)
                        overall_accuracy = (total_correct / total_questions * 100) if total_questions > 0 else 0
                        # st.text(f"Debug: {total_correct} correct out of {total_questions} questions")
                        st.markdown("""
                            <div class="metric-container" style="margin-top: 1rem;">
                                <div class="stat-header">Overall Performance</div>
                                <div class="stat-value">📈 {accuracy:.1f}%</div>
                            </div>
                        """.format(accuracy=overall_accuracy), unsafe_allow_html=True)

                    # Add Topics Overview with improved styling
                    st.markdown("### 📚 Current Topics")
                    
                    # Group topics to avoid repetition
                    unique_topics = {}
                    for topic, subtopic, _, _, _, _, _, _ in table_data:
                        if topic not in unique_topics:
                            unique_topics[topic] = []
                        unique_topics[topic].append(subtopic)
                    
                    for topic, subtopics in unique_topics.items():
                        st.markdown(f"""
                            <div style="
                                background-color: white;
                                border-radius: 8px;
                                padding: 15px 20px;
                                margin: 10px 0;
                                border-left: 4px solid #3b82f6;
                                box-shadow: 0 1px 2px rgba(0,0,0,0.05);">
                                <div style="
                                    color: #1f2937;
                                    font-size: 16px;
                                    font-weight: 600;
                                    margin-bottom: 8px;">
                                    {topic}
                                </div>
                                <div style="
                                    color: #6b7280;
                                    font-size: 14px;
                                    padding-left: 8px;
                                    border-left: 2px solid #e5e7eb;
                                    margin-left: 4px;">
                                    {subtopics[0]}
                                </div>
                            </div>
                        """, unsafe_allow_html=True)

                    # Practice Consistency Indicator
                    st.markdown("### Practice Consistency")
                    consistency_col1, consistency_col2 = st.columns([1, 2])
                    with consistency_col1:
                        if total_practice_days >= 5:
                            st.success("🌟 Excellent")
                        elif total_practice_days >= 3:
                            st.info("👍 Good")
                        else:
                            st.warning("⚠️ Needs Improvement")
                    with consistency_col2:
                        st.progress(min(total_practice_days/7, 1.0))  # Assumes 7 days as target

                with report_tabs[1]:
                    st.markdown("### Detailed Performance by {student_name}")
                    
                    # Convert table data to DataFrame with enhanced formatting
                    df = pd.DataFrame(table_data, columns=[
                        "Topic",
                        "Sub-Topic",
                        "Created Date",
                        "Deadline",
                        "Days Practiced",
                        "Easy Accuracy",
                        "Medium Accuracy",
                        "Hard Accuracy"
                    ])
                    
                    # Enhanced styling for the dataframe
                    st.dataframe(
                        df,
                        hide_index=True,
                        column_config={
                            "Topic": st.column_config.TextColumn(
                                "Topic",
                                help="Main subject area",
                                width="medium"
                            ),
                            "Sub-Topic": st.column_config.TextColumn(
                                "Sub-Topic",
                                help="Specific area of study",
                                width="medium"
                            ),
                            "Days Practiced": st.column_config.NumberColumn(
                                "Practice Days",
                                help="Number of days spent practicing",
                                format="%d days"
                            ),
                            "Easy Accuracy": st.column_config.TextColumn(
                                "Easy Level",
                                help="Performance in easy questions"
                            ),
                            "Medium Accuracy": st.column_config.TextColumn(
                                "Medium Level",
                                help="Performance in medium questions"
                            ),
                            "Hard Accuracy": st.column_config.TextColumn(
                                "Hard Level",
                                help="Performance in hard questions"
                            )
                        }
                    )

                with report_tabs[2]:
                    st.markdown("### Personalized Recommendations")
                    
                    # Create recommendations based on performance
                    if avg_accuracies[focus_needed_level] < 40:
                        st.error("#### Priority Areas for Improvement")
                        st.markdown("""
                            - 📚 **Additional practice needed** in {} difficulty questions
                            - 👨‍🏫 Consider scheduling **one-on-one sessions** with the teacher
                            - 🔄 Review fundamental concepts in challenging topics
                        """.format(focus_needed_level))
                        
                    elif avg_accuracies[focus_needed_level] < 70:
                        st.info("#### Suggested Focus Areas")
                        st.markdown("""
                            - 📝 Continue practicing {} level questions
                            - 🎯 Focus on topics with lower accuracy scores
                            - ✍️ Review incorrect answers to understand mistakes
                        """.format(focus_needed_level))
                        
                    else:
                        st.success("#### Keep Up the Great Work!")
                        st.markdown("""
                            - 🚀 Challenge yourself with harder questions
                            - 👥 Consider helping peers who might be struggling
                            - 📚 Explore more advanced topics
                        """)

                    # Add specific topic recommendations
                    st.markdown("### Topic-Specific Focus Areas")
                    for topic, subtopic, _, _, _, easy, medium, hard in table_data:
                        if any(acc.startswith('🔴') for acc in [easy, medium, hard]):
                            st.warning(f"**{topic} - {subtopic}**")
                            st.markdown("- Requires additional attention, especially in:")
                            if easy.startswith('🔴'):
                                st.markdown("  - Fundamental concepts")
                            if medium.startswith('🔴'):
                                st.markdown("  - Application problems")
                            if hard.startswith('🔴'):
                                st.markdown("  - Advanced concepts")


with tab6:
    view_questions()
