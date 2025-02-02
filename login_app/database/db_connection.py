from config import get_db

def get_user_collection():
    """Returns the users collection from the database."""
    db = get_db()
    return db["users"]  # Accessing the 'users' collection
