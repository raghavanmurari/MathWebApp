# In pages/student_list.py

import streamlit as st
from database.db_connection import get_user_collection, get_student_collection
import pandas as pd
from bson import ObjectId

def display_students(search_query=""):
    try:
        users = get_user_collection()
        students = get_student_collection()
        
        student_users = list(users.find({"role": "student"}))
        
        if not student_users:
            st.info("No students found")
            return
            
        data = []
        for user in student_users:
            student_info = students.find_one({"user_id": user["_id"]})
            data.append({
                "Name": user.get("name", "N/A"),
                "Email": user.get("email", "N/A"),
                "Parent Email": user.get("parent_email", "N/A"),
                "School": student_info.get("school", "N/A") if student_info else "N/A",
                "Grade": student_info.get("grade", "N/A") if student_info else "N/A",
                "Role": user.get("role", "N/A"),
                "Status": "Active" if user.get("active", True) else "Inactive"
            })
        
        df = pd.DataFrame(data)

        # ✅ Apply Search Filtering
        if search_query:
            df = df[
                df["Name"].str.contains(search_query, case=False, na=False) |
                df["Email"].str.contains(search_query, case=False, na=False)
            ]

        df.insert(0, "S.No", range(1, len(df) + 1))  # Add S.No Column
        st.dataframe(df.set_index("S.No"), use_container_width=True)

    except Exception as e:
        st.error(f"Error: {str(e)}")

