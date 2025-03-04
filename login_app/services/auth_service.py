from database.user_dao import find_user
from utils.security import verify_password

def authenticate_user(email, password):
    """Authenticates user and returns their role if credentials are valid."""
    # print(f"DEBUG: Attempting to authenticate {email}")
    
    user = find_user(email)
    
    if user is None:
        # print("DEBUG: User not found")
        return None

    # Check if user is active
    if not user.get('active', True):
        # print("DEBUG: User account is disabled")
        return "disabled"  # Special return value for disabled accounts

    if verify_password(password, user["password"]):
        return user["role"]

    # print("DEBUG: Password verification failed")
    return None