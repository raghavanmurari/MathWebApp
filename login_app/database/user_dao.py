from database.db_connection import get_user_collection
from utils.security import hash_password
from datetime import datetime
from bson.objectid import ObjectId
from database.student_dao import sync_student_data

def find_user(email):
    """Finds a user by email in a case-insensitive way."""
    try:
        users = get_user_collection()
        search_email = email.strip().lower()

        user = users.find_one(
            {"email": {"$regex": f"^{search_email}$", "$options": "i"}},
            {"_id": 1, "name": 1, "email": 1, "role": 1, "active": 1, "password": 1}
        )

        if not user:
            print(f"DEBUG: User not found - {search_email}")
            return None

        return user

    except Exception as e:
        print(f"ERROR in find_user: {str(e)}")
        return None

def find_users_by_name_pattern(name_pattern):
    """Find users whose name contains the given pattern."""
    try:
        users = get_user_collection()
        pattern = name_pattern.lower().strip()
        
        cursor = users.find({
            "name": {"$regex": pattern, "$options": "i"}  # Case-insensitive search
        })
        
        users_list = list(cursor)
        print(f"DEBUG: Found {len(users_list)} users matching name pattern: {pattern}")
        return users_list
        
    except Exception as e:
        print(f"ERROR in find_users_by_name_pattern: {str(e)}")
        return []

def get_all_users():
    """Fetch all users from the database."""
    users = get_user_collection()
    return list(users.find({}, {"_id": 0, "name": 1, "email": 1, "parent_email": 1, "role": 1, "active": 1}))

def save_user(user_data):
    """Saves a new user to the database with student sync."""
    try:
        users = get_user_collection()
        
        # Check if user exists
        existing_user = find_user(user_data.get('email'))
        if existing_user:
            print(f"DEBUG: User with email {user_data.get('email')} already exists.")
            return False
            
        # Ensure _id is ObjectId
        if '_id' not in user_data:
            user_data['_id'] = ObjectId()

        # Insert user
        result = users.insert_one(user_data)
        
        if result.inserted_id and user_data.get('role') == 'student':
            student_data = {
                'user_id': user_data['_id'],
                'grade': user_data['grade'],
                'school': user_data['school'],
                'created_at': datetime.utcnow(),
                'updated_at': datetime.utcnow()
            }
            sync_student_data(user_data, student_data)
            
        return result.inserted_id is not None
        
    except Exception as e:
        print(f"ERROR in save_user: {str(e)}")
        return False

def update_user(email, update_data):
    """Updates user details."""
    try:
        users = get_user_collection()
        email = email.lower().strip()
        
        # Get current user data
        user = find_user(email)
        if not user:
            return False
            
        # Update user
        update_data['updated_at'] = datetime.utcnow()
        update_result = users.update_one(
            {'email': email},
            {'$set': update_data}
        )
        
        # Sync with student collection if user is a student
        if update_result.modified_count > 0 and user.get('role') == 'student':
            updated_user = {**user, **update_data}
            sync_student_data(updated_user)
        
        return update_result.modified_count > 0
        
    except Exception as e:
        print(f"ERROR in update_user: {str(e)}")
        return False

def toggle_user_status(email, active_status):
    """Toggle user status with student sync."""
    try:
        user = find_user(email)
        if not user:
            print(f"DEBUG: User not found for email: {email}")
            return False
            
        update_data = {
            'active': active_status,
            'updated_at': datetime.utcnow()
        }
        
        # Update users collection
        users = get_user_collection()
        update_result = users.update_one(
            {'email': email.lower().strip()},
            {'$set': update_data}
        )
        
        # If user is student, sync the status
        if update_result.modified_count > 0 and user.get('role') == 'student':
            sync_student_data(user, {'active': active_status})
            
        return update_result.modified_count > 0
        
    except Exception as e:
        print(f"ERROR in toggle_user_status: {str(e)}")
        return False

def reset_password(email, new_password):
    """Reset user password."""
    try:
        users = get_user_collection()
        user = find_user(email)
        
        if not user:
            print(f"DEBUG: User not found for email: {email}")
            return False
            
        hashed_password = hash_password(new_password)
        update_data = {
            'password': hashed_password,
            'updated_at': datetime.utcnow()
        }
        
        update_result = users.update_one(
            {'email': email.lower().strip()},
            {'$set': update_data}
        )
        
        print(f"DEBUG: Password reset - matched: {update_result.matched_count}, modified: {update_result.modified_count}")
        return update_result.modified_count > 0
        
    except Exception as e:
        print(f"ERROR in reset_password: {str(e)}")
        return False