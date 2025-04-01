import streamlit as st
from database.db_connection import get_db
from bson.objectid import ObjectId
from datetime import datetime, timedelta

def show_create_assignment():
    st.subheader("Create New Assignment")
    
    # Get database connections
    db = get_db()
    topics_collection = db['topics']
    
    # Step 1: Topic and Sub-topic Selection
    if 'create_step' not in st.session_state:
        st.session_state['create_step'] = 1
    
    # Get topics and create selection
    topics = list(topics_collection.find({}, {"_id": 1, "name": 1, "sub_topics": 1}))
    topic_options = {str(topic['_id']): topic['name'] for topic in topics}
    
    selected_topic_id = st.selectbox(
        "Select Topic",
        options=list(topic_options.keys()),
        format_func=lambda x: topic_options[x]
    )
    
    if selected_topic_id:
        selected_topic = topics_collection.find_one({"_id": ObjectId(selected_topic_id)})
        if selected_topic and 'sub_topics' in selected_topic:
            sub_topics = selected_topic['sub_topics']
            selected_sub_topics = st.multiselect(
                "Select Sub-Topics",
                options=sub_topics,
                default=None
            )
            
            if selected_sub_topics:
                if st.button("Continue to Student Selection"):
                    st.session_state['topic_id'] = selected_topic_id
                    st.session_state['sub_topics'] = selected_sub_topics
                    st.session_state['create_step'] = 2
                    st.rerun()

    # Step 2: Student Selection and Deadline
    if st.session_state.get('create_step') == 2:
        st.markdown("---")
        st.subheader("Select Students and Set Deadline")
        
        # Get students grouped by grade
        students_collection = db['students']
        users_collection = db['users']
        
        students = list(students_collection.find({"active": True}))
        student_grades = {}
        
        for student in students:
            grade = student.get('grade')
            if grade not in student_grades:
                student_grades[grade] = []
            
            # Get user info
            user = users_collection.find_one({"_id": student['user_id']})
            if user:
                student_info = {
                    'id': str(student['_id']),
                    'name': user.get('name', 'Unknown'),
                    'grade': grade
                }
                student_grades[grade].append(student_info)
        
        # Create grade-wise student selection
        selected_students = []
        for grade in sorted(student_grades.keys()):
            st.write(f"Grade {grade}")
            
            # Select all checkbox for this grade
            grade_students = student_grades[grade]
            grade_student_names = [s['name'] for s in grade_students]
            
            col1, col2 = st.columns([0.1, 0.9])
            with col1:
                select_all = st.checkbox(f"All", key=f"all_{grade}")
            
            with col2:
                if select_all:
                    selected = grade_student_names
                    st.write("All students selected")
                else:
                    selected = st.multiselect(
                        "Select students",
                        options=grade_student_names,
                        key=f"grade_{grade}"
                    )
            
            # Add selected students to the list
            for student in grade_students:
                if student['name'] in selected:
                    selected_students.append(student['id'])
        
        # Deadline selection
        st.markdown("---")
        col1, col2 = st.columns(2)
        with col1:
            deadline_date = st.date_input(
                "Select Deadline Date",
                min_value=datetime.now().date(),
                value=datetime.now().date() + timedelta(days=7)
            )
        with col2:
            deadline_time = st.time_input(
                "Select Deadline Time",
                value=datetime.strptime("23:59", "%H:%M").time()
            )
        
        deadline = datetime.combine(deadline_date, deadline_time)
        
        # Create Assignment button
        if selected_students:
            if st.button("Create Assignment", type="primary"):
                assignments_collection = db['assignments']
                
                # Duplicate check: ensure one sub-topic per student
                duplicate_found = False
                duplicates = []

                # We'll need these collections here:
                students_collection = db['students']
                users_collection = db['users']

                for s_id in selected_students:
                    # 1. Look up the student's name right now:
                    student_doc = students_collection.find_one({"_id": ObjectId(s_id)})
                    if student_doc:
                        user_doc = users_collection.find_one({"_id": student_doc["user_id"]})
                        student_name = user_doc["name"] if user_doc else "Unknown"
                    else:
                        student_name = "Unknown"
                    
                    # 2. For each sub-topic, see if there’s a duplicate:
                    for sub_topic in st.session_state['sub_topics']:
                        existing = assignments_collection.find_one({
                            "teacher_id": ObjectId(st.session_state["user_id"]),
                            "topic_id": ObjectId(st.session_state['topic_id']),
                            "sub_topics": sub_topic,
                            "students": ObjectId(s_id)
                        })
                        if existing:
                            duplicate_found = True
                            duplicates.append(f"{student_name} already has the sub-topic '{sub_topic}' assigned")

                # If we found any duplicates, display them
                if duplicate_found:
                    st.warning("The following students already have this sub-topic assigned: " + ", ".join(duplicates))
                else:
                    # Create separate assignments for each sub-topic
                    created_count = 0
                    for sub_topic in st.session_state['sub_topics']:
                        new_assignment = {
                            "teacher_id": ObjectId(st.session_state["user_id"]),
                            "students": [ObjectId(s_id) for s_id in selected_students],
                            "topic_id": ObjectId(st.session_state['topic_id']),
                            "sub_topics": [sub_topic],  # Just one sub-topic per assignment
                            "deadline": deadline,
                            "status": "active",
                            "created_at": datetime.now()
                        }
                        
                        # Insert assignment
                        assignments_collection.insert_one(new_assignment)
                        created_count += 1
                    
                    st.success(f"{created_count} assignment(s) created successfully!")
                    
                    # Clear create assignment state
                    for key in ['create_step', 'topic_id', 'sub_topics', 'show_create']:
                        if key in st.session_state:
                            del st.session_state[key]
                    st.rerun()

        else:
            st.warning("Please select at least one student")

        if st.button("Cancel"):
            for key in ['create_step', 'topic_id', 'sub_topics', 'show_create']:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()