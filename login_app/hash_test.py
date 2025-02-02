from utils.security import hash_password

hashed_password = hash_password("Admin@123")
print("Manually Hashed Password:", hashed_password)
