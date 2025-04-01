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

def get_days_practiced_color(days_str):
    """Returns color-coded days practiced indicator based on percentage."""
    # Parse the "X out of Y days" format
    parts = days_str.split("out of")
    practiced = int(parts[0].strip())
    total = int(parts[1].strip().split(" days")[0])
    
    # Calculate percentage
    percentage = (practiced / total) * 100 if total > 0 else 0
    
    # Apply color coding based on percentage
    if percentage < 40:
        return "🔴 " + days_str
    elif percentage <= 70:
        return "🟡 " + days_str
    else:
        return "🟢 " + days_str

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
            question_counts = {}
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
                    # Create a unique key for this topic and subtopic combination
                        topic_subtopic_key = f"{topic_name}_{sub_topic}"
                        
                        # Initialize counts for this topic/subtopic
                        if topic_subtopic_key not in question_counts:
                            question_counts[topic_subtopic_key] = {
                                "easy_attempted": 0,
                                "easy_correct": 0,
                                "medium_attempted": 0,
                                "medium_correct": 0,
                                "hard_attempted": 0,
                                "hard_correct": 0
                            }
                        for difficulty in ["Easy", "Medium", "Hard"]:
                            difficulty_responses = [r for r in subtopic_responses 
                                if questions[str(r["question_id"])].get("difficulty") == difficulty]
                            correct = sum(1 for r in difficulty_responses if r.get("is_correct"))
                            total = len(difficulty_responses)
                            accuracy = (correct / total * 100) if total > 0 else 0
                            
                            # Store accuracy and counts without modifying table_data structure
                            if difficulty == "Easy":
                                easy_accuracy = accuracy
                                question_counts[topic_subtopic_key]["easy_attempted"] = total
                                question_counts[topic_subtopic_key]["easy_correct"] = correct
                            elif difficulty == "Medium":
                                medium_accuracy = accuracy
                                question_counts[topic_subtopic_key]["medium_attempted"] = total
                                question_counts[topic_subtopic_key]["medium_correct"] = correct
                            else:
                                hard_accuracy = accuracy
                                question_counts[topic_subtopic_key]["hard_attempted"] = total
                                question_counts[topic_subtopic_key]["hard_correct"] = correct

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

# Replace the existing report section with this updated version:
has_assignments = len(active_assignments) > 0 and len(topic_subtopic_options) > 1
if st.button("Generate Report", key=f"progress_report_{student_id}", disabled=not has_assignments):
    # NEW CODE: Create a set to track all unique practice days across all topics
    all_unique_practice_dates = set()
    
    # NEW CODE: Populate this set by collecting all practice dates from all responses
    for assignment in active_assignments:
        responses = list(responses_collection.find({
            "student_id": ObjectId(student_id),
            "assignment_id": assignment["_id"]
        }))
        practice_dates = {r.get("timestamp").date() for r in responses if r.get("timestamp")}
        all_unique_practice_dates.update(practice_dates)
    
    # NEW CODE: Store the total unique practice days in session state
    total_unique_days = len(all_unique_practice_dates)
    st.session_state['total_unique_days_practiced'] = total_unique_days
    
    report_tabs = st.tabs(["Details 📝", "Parent Summary 📱"])

    # Existing detailed report tab
    with report_tabs[0]:
        st.markdown(f"### Detailed Performance by {student_name}")
        if not table_data:
            st.info("No assignments available for this student.")
        else:
            new_table_data = []
            for row in table_data:
                topic, sub_topic, created_str, deadline_str, days_practiced, easy_acc, medium_acc, hard_acc = row
                
                # Add these lines to get question counts for this topic/subtopic
                topic_subtopic_key = f"{topic}_{sub_topic}"
                counts = question_counts.get(topic_subtopic_key, {
                    "easy_attempted": 0, "easy_correct": 0,
                    "medium_attempted": 0, "medium_correct": 0,
                    "hard_attempted": 0, "hard_correct": 0
                })

                # Keep your existing code for date parsing
                try:
                    created_date = datetime.strptime(created_str, "%Y-%m-%d")
                    deadline_date = datetime.strptime(deadline_str, "%Y-%m-%d")
                except ValueError:
                    days_total_subtopic = 1
                else:
                    days_total_subtopic = (deadline_date - created_date).days + 1
                    if days_total_subtopic < 1:
                        days_total_subtopic = 1

                # Format days practiced as before
                new_days_practiced = f"{days_practiced} out of {days_total_subtopic} days"
                colored_days = get_days_practiced_color(new_days_practiced)
                
                # Add these lines to format accuracy with question counts
                easy_counts = f"{easy_acc} ({counts['easy_correct']}/{counts['easy_attempted']})"
                medium_counts = f"{medium_acc} ({counts['medium_correct']}/{counts['medium_attempted']})"
                hard_counts = f"{hard_acc} ({counts['hard_correct']}/{counts['hard_attempted']})"
                
                # Now modify the new_table_data append to use the count-enhanced accuracy
                new_table_data.append([
                    topic,
                    sub_topic,
                    created_str,
                    deadline_str,
                    colored_days,
                    easy_counts,
                    medium_counts,
                    hard_counts
                ])

            # Keep the DataFrame creation and display as is
            df = pd.DataFrame(new_table_data, columns=[
                "Topic",
                "Sub-Topic",
                "Created Date",
                "Deadline",
                "Days Practiced",
                "Easy Accuracy",
                "Medium Accuracy",
                "Hard Accuracy"
            ])

            st.dataframe(df, hide_index=True)

    # New parent summary report tab
    with report_tabs[1]:
        st.markdown(f"### {student_name}'s Learning Progress")
        
        if not table_data:
            st.info("No assignments available for this student.")
        else:
            # ... Existing CSS styles ...
            
            # Create parent summary data
            parent_summary_data = []
            
            # Get the questions collection to count questions
            questions_collection = db["questions"]
            
            for assignment in active_assignments:
                topic_id = assignment.get("topic_id")
                topic_name = "Unknown Topic"
                if topic_id:
                    topic_doc = topics_collection.find_one({"_id": ObjectId(str(topic_id))})
                    if topic_doc:
                        topic_name = topic_doc.get("name")
                
                for sub_topic in assignment.get("sub_topics", []):
                    current_combo = f"{topic_name} - {sub_topic}"
                    if "All Topics" not in selected_topic_subtopics and current_combo not in selected_topic_subtopics:
                        continue
                    
                    # Count total questions for this subtopic in the assignment
                    total_questions = questions_collection.count_documents({
                        "topic_id": topic_id,
                        "sub_topic": sub_topic
                    })
                    
                    # Get student responses for this assignment
                    responses = list(responses_collection.find({
                        "student_id": ObjectId(student_id),
                        "assignment_id": assignment["_id"]
                    }))
                    
                    # Filter responses for this subtopic
                    subtopic_responses = []
                    for response in responses:
                        question = questions_collection.find_one({"_id": response["question_id"]})
                        if question and question.get("sub_topic") == sub_topic:
                            subtopic_responses.append(response)
                    
                    # Count attempted and correct questions
                    attempted_questions = len(subtopic_responses)
                    correct_questions = sum(1 for r in subtopic_responses if r.get("is_correct"))
                    
                    # Calculate completion percentage
                    completion_percentage = (attempted_questions / total_questions * 100) if total_questions > 0 else 0
                    accuracy_percentage = (correct_questions / attempted_questions * 100) if attempted_questions > 0 else 0
                    
                    # Calculate days practiced
                    practice_dates = {r.get("timestamp").date() for r in subtopic_responses if r.get("timestamp")}
                    num_practice_days = len(practice_dates)
                    
                    # Calculate total days student was supposed to practice
                    created_date = assignment.get("created_at").date() if assignment.get("created_at") else datetime.now().date()
                    deadline_date = assignment.get("deadline").date() if assignment.get("deadline") else datetime.now().date()
                    total_practice_days = (deadline_date - created_date).days + 1  # +1 to make it inclusive
                    if total_practice_days < 1:
                        total_practice_days = 1
                    
                    # Store practice dates for later checking
                    if 'subtopic_practice_days' not in st.session_state:
                        st.session_state['subtopic_practice_days'] = {}
                    
                    subtopic_key = f"{topic_name}_{sub_topic}"
                    st.session_state['subtopic_practice_days'][subtopic_key] = practice_dates
                    
                    parent_summary_data.append({
                        "Topic": topic_name,
                        "Sub-Topic": sub_topic,
                        "Total Questions": total_questions,
                        "Attempted": attempted_questions,
                        "Correct": correct_questions,
                        "Days Practiced": num_practice_days,
                        "Total Days": total_practice_days,  # Add this line
                        "Completion": completion_percentage,
                        "Accuracy": accuracy_percentage
                    })
            
            # Display parent summary cards
            if parent_summary_data:
                # Create and display the parent summary table
                df_parent = pd.DataFrame(parent_summary_data)  # Create DataFrame from the data
                
                # Format the table columns
                # st.markdown("### Topic-wise Summary")
                st.dataframe(
                    df_parent[["Topic", "Sub-Topic", "Total Questions", "Attempted", "Correct", "Days Practiced", "Total Days"]],  # Include "Total Days"
                    hide_index=True,
                    column_config={
                        "Topic": st.column_config.TextColumn("Topic"),
                        "Sub-Topic": st.column_config.TextColumn("Sub-Topic"),
                        "Total Questions": st.column_config.NumberColumn("Total Questions", format="%d"),
                        "Attempted": st.column_config.NumberColumn("Attempted", format="%d"),
                        "Correct": st.column_config.NumberColumn("Correct", format="%d"),
                        "Days Practiced": st.column_config.NumberColumn("Days Practiced", format="%d", help="Number of unique days the student worked on this topic"),
                        "Total Days": st.column_config.NumberColumn("Total Days", format="%d", help="Number of days student was supposed to practice (from created date to deadline)")
                    },
                    use_container_width=True
                )
                
                # Add a legend/explanation for metrics
                st.markdown("""
                    <div style="background-color: #f9f9f9; padding: 15px; border-radius: 5px; margin-top: 20px; border-left: 3px solid #4CAF50;">
                        <h4 style="margin-top: 0;">Understanding the Metrics</h4>
                        <ul>
                            <li><strong>Total Questions</strong>: The total number of questions available for practice in this topic</li>
                            <li><strong>Attempted</strong>: How many questions the student has tried so far</li>
                            <li><strong>Correct</strong>: How many questions the student answered correctly</li>
                            <li><strong>Days Practiced</strong>: Number of unique days the student worked on this topic</li>
                            <li><strong>Total Days</strong>: Number of days student was supposed to practice (from created date to deadline)</li>
                        </ul>
                    </div>
                """, unsafe_allow_html=True)
            else:
                st.info("No data available to generate parent summary.")

with tab6:
    view_questions()