from database.db_connection import get_user_collection

def get_all_students():
    """Fetch all students from the database."""
    try:
        users = get_user_collection()
        students = users.find({"role": "student"}, {"name": 1, "email": 1, "parent_email": 1, "role": 1, "active": 1, "_id": 0})
        return list(students)
    except Exception as e:
        print(f"ERROR in get_all_students: {str(e)}")
        return []
