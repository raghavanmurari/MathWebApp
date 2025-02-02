from database.db_connection import get_user_collection
from utils.security import hash_password
from datetime import datetime

def find_user(email):
    """Finds a user by email in a case-insensitive way."""
    try:
        users = get_user_collection()
        search_email = email.strip().lower()
        
        print(f"DEBUG: Attempting to find email: '{search_email}'")
        
        # First, let's see what's in our collection
        cursor = users.find({}, {"email": 1, "_id": 0})
        all_emails = [doc["email"] for doc in cursor]
        print(f"DEBUG: All emails in database: {all_emails}")
        
        # Try the exact find
        user = users.find_one({"email": search_email})
        print(f"DEBUG: Direct match result: {user}")
        
        return user
        
    except Exception as e:
        print(f"ERROR in find_user: {str(e)}")
        return None

def find_users_by_name_pattern(name_pattern):
    """Find users whose name contains the given pattern."""
    try:
        users = get_user_collection()
        pattern = name_pattern.lower().strip()
        
        # Find users where name contains the pattern
        cursor = users.find({
            "name": {"$regex": pattern, "$options": "i"}  # Case-insensitive name search
        })
        
        # Convert cursor to list and return
        users_list = list(cursor)
        print(f"DEBUG: Found {len(users_list)} users matching name pattern: {pattern}")
        return users_list
        
    except Exception as e:
        print(f"ERROR in find_users_by_name_pattern: {str(e)}")
        return []

def save_user(user_data):
    """Saves a new user to the database, ensuring email uniqueness."""
    users = get_user_collection()
    
    # Check if the user already exists
    existing_user = find_user(user_data.get("email"))
    if existing_user:
        print(f"DEBUG: User with email {user_data.get('email')} already exists.")
        return False

    users.insert_one(user_data)
    print(f"DEBUG: New user {user_data.get('email')} saved successfully.")
    return True

def delete_user(email):
    """Deletes a user from the database."""
    try:
        users = get_user_collection()
        result = users.delete_one({"email": email.lower().strip()})
        print(f"DEBUG: Delete user result: {result.deleted_count}")
        return result.deleted_count > 0
    except Exception as e:
        print(f"ERROR in delete_user: {str(e)}")
        return False

def update_user(email, update_data):
    try:
        users = get_user_collection()
        existing_user = find_user(email)
        if not existing_user:
            return False
        
        update_result = users.update_one(
            {"email": {"$regex": f"^{email}$", "$options": "i"}},
            {"$set": update_data}
        )
        
        return update_result.modified_count > 0
    except Exception as e:
        print(f"ERROR in update_user: {str(e)}")
        return False


def toggle_user_status(email, active_status):
    """Toggle user's active status."""
    try:
        users = get_user_collection()
        email = email.lower().strip()
        
        print(f"DEBUG: Attempting to toggle status for {email} to {active_status}")
        
        # First verify user exists
        user = find_user(email)
        if not user:
            print(f"DEBUG: User {email} not found")
            return False
            
        # Update the user status
        result = users.update_one(
            {"email": email.lower().strip()},
            {
                "$set": {
                    "active": active_status,
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        print(f"DEBUG: Update result - matched count: {result.matched_count}, modified count: {result.modified_count}")
        return result.modified_count > 0
        
    except Exception as e:
        print(f"ERROR in toggle_user_status: {str(e)}")
        print(f"Exception details: {str(e.__dict__)}")
        return False