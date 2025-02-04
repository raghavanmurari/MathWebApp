import sys
import os
from datetime import datetime

# Add parent directory to Python path so we can import database module
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

from database.db_connection import get_user_collection

def update_user_schema():
    try:
        users = get_user_collection()
        print("Connected to database successfully")
        
        # Update teacher and admin users
        teacher_admin_result = users.update_many(
            {"role": {"$in": ["teacher", "admin"]}},  # Match teachers and admins
            {
                "$set": {
                    "parent_email": None,  # Set parent_email to None for teachers/admins
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        # Update student users
        student_result = users.update_many(
            {"role": "student"},  # Match students
            {
                "$set": {
                    "parent_email": "",  # Empty string for students, to be updated later
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        print(f"\nUpdated {teacher_admin_result.modified_count} teacher/admin users")
        print(f"Updated {student_result.modified_count} student users")
        
        # Print all users to verify
        print("\nUpdated users in database:")
        all_users = users.find()
        for user in all_users:
            print("\nUser document:")
            print(f"Email: {user.get('email')}")
            print(f"Role: {user.get('role')}")
            print(f"Name: {user.get('name')}")
            print(f"Gender: {user.get('gender')}")
            print(f"Active: {user.get('active')}")
            print(f"Parent Email: {user.get('parent_email')}")
            print(f"Created at: {user.get('created_at')}")
            print(f"Updated at: {user.get('updated_at')}")
            print("-" * 50)

    except Exception as e:
        print(f"Error updating schema: {str(e)}")

if __name__ == "__main__":
    print("Starting schema update...")
    update_user_schema()
    print("\nSchema update completed!")