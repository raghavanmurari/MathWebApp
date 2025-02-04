from database.db_connection import get_student_collection
from datetime import datetime
from bson.objectid import ObjectId

def find_student_by_user_id(user_id):
    """Find a student by their user_id."""
    try:
        students = get_student_collection()
        if isinstance(user_id, str):
            user_id = ObjectId(user_id)
        return students.find_one({"user_id": user_id})
    except Exception as e:
        print(f"ERROR in find_student_by_user_id: {str(e)}")
        return None

def save_student(student_data):
    """Save a new student record."""
    try:
        # Only proceed if this is a student role
        if student_data.get('role') != 'student':
            print("DEBUG: Not a student role, skipping student collection")
            return True
            
        # Check for required fields
        if not student_data.get('grade') or not student_data.get('school'):
            print("ERROR: Missing required student data (grade or school)")
            return False
            
        students = get_student_collection()
        
        # Prepare student record with only necessary fields
        student_record = {
            'user_id': student_data['_id'],
            'grade': student_data['grade'],
            'school': student_data['school'],
            'active': student_data.get('active', True),
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        }
            
        result = students.insert_one(student_record)
        return result.inserted_id is not None
    except Exception as e:
        print(f"ERROR in save_student: {str(e)}")
        return False

def update_student(user_id, update_data):
    """Update student details in the database."""
    try:
        students = get_student_collection()
        if isinstance(user_id, str):
            user_id = ObjectId(user_id)
            
        update_data['updated_at'] = datetime.utcnow()
        update_result = students.update_one(
            {"user_id": user_id},
            {"$set": update_data}
        )
        return update_result.modified_count > 0
    except Exception as e:
        print(f"ERROR in update_student: {str(e)}")
        return False

def sync_student_data(user_data, student_specific_data=None):
    """Synchronize student data when user data is updated."""
    try:
        if user_data.get('role') != 'student':
            return True
            
        # Ensure we have student_specific_data with required fields for new students
        if not student_specific_data:
            print("DEBUG: No student specific data provided for sync")
            return False
            
        # Validate required fields are present and not null
        if not student_specific_data.get('grade') or not student_specific_data.get('school'):
            print("ERROR: Missing required student data (grade or school)")
            return False
            
        students = get_student_collection()
        user_id = user_data['_id']
        if isinstance(user_id, str):
            user_id = ObjectId(user_id)
            
        update_data = {
            'grade': student_specific_data['grade'],
            'school': student_specific_data['school'],
            'updated_at': datetime.utcnow()
        }
        
        # Keep active status in sync if present
        if 'active' in user_data:
            update_data['active'] = user_data['active']
        
        result = students.update_one(
            {'user_id': user_id},
            {'$set': update_data},
            upsert=True
        )
        
        return result.modified_count > 0 or result.upserted_id is not None
    except Exception as e:
        print(f"ERROR in sync_student_data: {str(e)}")
        return False