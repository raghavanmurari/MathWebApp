# In pages/student_list.py

import streamlit as st
from database.db_connection import get_user_collection, get_student_collection
import pandas as pd
from bson import ObjectId

def display_students():
    try:
        users = get_user_collection()
        students = get_student_collection()
        
        # Get all student users
        student_users = list(users.find({"role": "student"}))
        
        if not student_users:
            st.info("No students found")
            return
            
        # Create DataFrame with required columns
        data = []
        for user in student_users:
            student_info = students.find_one({"user_id": user["_id"]})
            data.append({
                "Name": user.get("name", "N/A"),
                "Email": user.get("email", "N/A"),
                "Parent Email": user.get("parent_email", "N/A"),
                "Role": user.get("role", "N/A"),
                "Status": "Active" if user.get("active", True) else "Inactive"
            })
        
        df = pd.DataFrame(data)
        st.dataframe(df, use_container_width=True)
        
    except Exception as e:
        st.error(f"Error: {str(e)}")