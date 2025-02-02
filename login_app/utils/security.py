import bcrypt

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