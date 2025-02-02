import pymongo

# MongoDB Connection URI (Update with Atlas URI if needed)
MONGO_URI = "mongodb://localhost:27017"  # Change if using MongoDB Atlas
DB_NAME = "adaptive_math_db"  # New unified database

def get_db():
    """Returns the database connection."""
    client = pymongo.MongoClient(MONGO_URI)
    return client[DB_NAME]
