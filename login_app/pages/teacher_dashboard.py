import streamlit as st
from utils.session_manager import clear_session, load_session
from pages.student_list import display_students
from pages.display_question_bank import display_question_bank, get_db  
from database.db_connection import get_assignment_collection
from bson.objectid import ObjectId  
from pages.create_assignment import show_create_assignment

# ✅ Remove Sidebar & Set Page Config
st.set_page_config(
    page_title="Teacher Dashboard",
    page_icon="🎓",
    layout="wide",
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
    </style>
    """,
    unsafe_allow_html=True
)

load_session()

if not st.session_state.logged_in:
    st.switch_page("pages/login_page.py")

col1, col2 = st.columns([0.9, 0.1])
with col1:
    st.title("🎓 Teacher Dashboard")
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

with tab1:
    st.header("Welcome to the Teacher Dashboard")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(label="Total Students", value="25", delta="2 new")
    with col2:
        st.metric(label="Active Assignments", value="8", delta="-1")
    with col3:
        st.metric(label="Average Score", value="85%", delta="+5%")

with tab2:
    st.header("Student Management")
    search_query = st.text_input("🔍 Search Students by Name or Email")
    display_students()

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

                sub_topics = ", ".join(assignment.get("sub_topics", ["No sub-topics"]))
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
                    "Sub-Topics": sub_topics,
                    "Deadline": deadline,
                    "Status": status,
                    "Assigned Students": assigned_students,
                    "Student User IDs": assigned_student_ids  # ✅ Display student user IDs
                })

            if assignment_data:
                st.dataframe(
                    assignment_data,
                    use_container_width=True,
                    column_config={
                        "Sub-Topics": st.column_config.TextColumn("Sub-Topics"),
                        "Deadline": st.column_config.TextColumn("Deadline"),
                        "Status": st.column_config.TextColumn("Status", width="small"),
                        "Assigned Students": st.column_config.TextColumn("Assigned Students"),
                        "Student User IDs": st.column_config.TextColumn("Student User IDs")  # ✅ New Column
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
    st.header("Student Progress")
    st.write("Progress tracking and analytics will be displayed here")
