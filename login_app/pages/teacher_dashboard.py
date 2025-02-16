import streamlit as st
from utils.session_manager import clear_session, load_session
from pages.student_list import display_students
from pages.display_question_bank import display_question_bank, get_db  
from database.db_connection import get_user_collection, get_assignment_collection
from bson.objectid import ObjectId  
from pages.create_assignment import show_create_assignment
from utils.progress_tracking import ProgressTracker
import pandas as pd


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

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🏠 Dashboard",
    "👩‍🏫 Students",
    "📚 Question Bank",
    "📝 Assignments",
    "📊 Progress"
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
    # col1, col2, col3 = st.columns(3)
    col1, col2 = st.columns(2)
    with col1:
        st.metric(label="Total Students", value=total_students)
    with col2:
        st.metric(label="Active Assignments", value=active_assignments)
    # with col3:
    #     st.metric(label="Average Score", value="85%", delta="+5%")  # Placeholder, update later

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
                # sub_topics = ", ".join(assignment.get("sub_topics", ["No sub-topics"]))
                # Instead of joining them, just get the sub_topics list
                subtopics_list = assignment.get("sub_topics", ["No sub-topics"])
                for single_subtopic in subtopics_list:
                    created_str = assignment.get("created_at").strftime("%Y-%m-%d %H:%M") if assignment.get("created_at") else "No date"
                    deadline_str = assignment.get("deadline").strftime("%Y-%m-%d %H:%M") if assignment.get("deadline") else "No deadline"

                deadline = assignment.get("deadline", "No deadline").strftime("%Y-%m-%d %H:%M") if assignment.get("deadline") else "No deadline"
                status = assignment.get("status", "Unknown")

                # ✅ Fetch Student Names and User IDs
                student_names = []
                student_user_ids = []

                student_ids = assignment.get("students", [])
                if student_ids:
                    for student_id in student_ids:
                        try:
                            # Fetch student details from `students` collection
                            student_doc = students_collection.find_one({"_id": ObjectId(str(student_id))})
                            if student_doc:
                                user_id = student_doc.get("user_id")

                                # Fetch user details from `users` collection using user_id
                                user_doc = users_collection.find_one({"_id": ObjectId(str(user_id))})
                                if user_doc:
                                    student_names.append(user_doc.get("name", "Unknown Student"))
                                    student_user_ids.append(str(user_id))  # ✅ Display correct `user_id`
                                else:
                                    student_names.append("No student found")
                                    student_user_ids.append(str(user_id))
                            else:
                                student_names.append("No student found")
                                student_user_ids.append("N/A")
                        except Exception as e:
                            student_names.append(f"Error: {str(e)}")
                            student_user_ids.append("N/A")

                assigned_students = ", ".join(student_names) if student_names else "No students assigned"
                assigned_student_ids = ", ".join(student_user_ids) if student_user_ids else "No students assigned"

                assignment_data.append({
                    "Topic": topic_name,  # Add Topic as first column
                    "Sub-Topics": single_subtopic,
                    "Created": assignment.get("created_at").strftime("%Y-%m-%d %H:%M") if assignment.get("created_at") else "No date",
                    "Deadline": deadline,
                    "Status": status,
                    "Assigned Students": assigned_students,
                    "Grade": assignment.get("grade", "N/A")  # If you don't have a grade field yet, use "N/A"
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
    st.header("📊 Student Progress")

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
                # Use a multiselect instead of a selectbox.
                selected_topic_subtopics = st.multiselect(
                    "Select one or more Topic - Subtopic combinations:",
                    options=topic_subtopic_options,
                    default=["All Topics"]  # Default selection can be "All Topics"
                )
            else:
                st.warning("No topics found for this student.")
                selected_topic_subtopics = ["All Topics"]

        # with col2:
        #     if len(topic_subtopic_options) > 1:
        #         selected_topic_subtopic = st.selectbox(
        #             "Select Topic - Subtopic:",
        #             options=topic_subtopic_options
        #         )
        #     else:
        #         st.warning("No topics found for this student.")
        #         selected_topic_subtopic = None

        if student_id:
            student_name = students_dict[student_id]
            st.subheader(f"Progress for {student_name}")

            if not active_assignments:
                st.warning("No active assignments for this student.")
            else:
                st.write("### Performance Analysis")
                table_data = []
                
                for assignment in active_assignments:
                    # Get topic name
                    topic_id = assignment.get("topic_id")
                    topic_name = "Unknown Topic"
                    if topic_id:
                        topic_doc = topics_collection.find_one({"_id": ObjectId(str(topic_id))})
                        if topic_doc:
                            topic_name = topic_doc.get("name")

                    # Get responses for this assignment
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

                    # Calculate accuracies for each difficulty level
                    for sub_topic in assignment.get("sub_topics", []):
                        # Skip if the current combination is not selected
                        current_combo = f"{topic_name} - {sub_topic}"
                        if "All Topics" not in selected_topic_subtopics and current_combo not in selected_topic_subtopics:
                            continue

                        # Filter responses by subtopic
                        subtopic_responses = [r for r in responses 
                            if str(r["question_id"]) in questions 
                            and questions[str(r["question_id"])].get("sub_topic") == sub_topic]

                        # Calculate accuracies for each difficulty level
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

                        # Count practice days
                        practice_dates = {r.get("timestamp").date() for r in subtopic_responses if r.get("timestamp")}
                        num_practice_days = len(practice_dates)

                        # Format dates
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
                    # Convert to DataFrame and display
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

                    # Display using Streamlit
                    st.dataframe(df, hide_index=True)
                else:
                    st.info("No data available for the selected filters.")