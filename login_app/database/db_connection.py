from config import get_db  # ✅ Import shared DB connection from config.py

def get_database():
    """Returns the database connection."""
    return get_db()  # ✅ Use shared DB connection

def get_user_collection():
    """Returns the users collection from the database."""
    db = get_db()
    return db["users"]

def get_student_collection():
    """Returns the students collection from the database."""
    db = get_db()
    return db["students"]

def get_assignment_collection():
    """Returns the assignments collection from the database."""
    db = get_db()
    return db["assignments"]

def get_question_collection():
    """Returns the questions collection from the database."""
    db = get_db()
    return db["questions"]  # ✅ New function to fetch the questions collection
