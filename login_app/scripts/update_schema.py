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
        
        # Update all existing users
        result = users.update_many(
            {},  # Match all documents
            {
                "$set": {
                    "name": "Default User",
                    "gender": "other",
                    "active": True,
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        print(f"\nUpdated {result.modified_count} users")
        
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
            print(f"Created at: {user.get('created_at')}")
            print(f"Updated at: {user.get('updated_at')}")
            print("-" * 50)

    except Exception as e:
        print(f"Error updating schema: {str(e)}")

if __name__ == "__main__":
    print("Starting schema update...")
    update_user_schema()
    print("\nSchema update completed!")