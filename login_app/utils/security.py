import bcrypt
import re

def validate_password(password: str) -> bool:
    """
    Check that the password:
    - is at least 8 characters long
    - contains at least one uppercase letter
    - contains at least one lowercase letter
    - contains at least one digit
    - contains at least one special character
    """
    if len(password) < 8:
        return False
    if not re.search(r'[A-Z]', password):
        return False
    if not re.search(r'[a-z]', password):
        return False
    if not re.search(r'\d', password):
        return False
    if not re.search(r'[\W_]', password):  # Matches any non-alphanumeric character
        return False
    return True

def hash_password(password):
    """Hashes a password using bcrypt."""
    try:
        print(f"DEBUG: Attempting to hash password")
        hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
        print(f"DEBUG: Password successfully hashed: {hashed[:20]}...")  # Show first 20 chars of hash
        return hashed
    except Exception as e:
        print(f"ERROR: Password hashing failed → {e}")
        return None

def verify_password(password, hashed_password):
    """Verifies if the provided password matches the stored hash."""
    try:
        print(f"DEBUG: Starting password verification")
        print(f"DEBUG: Password length: {len(password)}")
        print(f"DEBUG: Hash length: {len(hashed_password)}")
        
        match = bcrypt.checkpw(password.encode("utf-8"), hashed_password.encode("utf-8"))
        print(f"DEBUG: Password verification result: {match}")
        return match
    except Exception as e:
        print(f"ERROR: Password verification failed → {e}")
        print(f"ERROR details: {str(e)}")
        return False