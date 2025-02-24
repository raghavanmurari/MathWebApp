# import pymongo

# # MongoDB Connection URI (Update with Atlas URI if needed)
# MONGO_URI = "mongodb://localhost:27017"  # Change if using MongoDB Atlas
# DB_NAME = "adaptive_math_db"  # New unified database

# def get_db():
#     """Returns the database connection."""
#     client = pymongo.MongoClient(MONGO_URI)
#     return client[DB_NAME]


import streamlit as st
import pymongo
import os

# Use the MongoDB Atlas URI from Streamlit secrets if available,
# otherwise fall back to the local URI (for development)
# MONGO_URI = st.secrets["mongodb"]["uri"] if "mongodb" in st.secrets else "mongodb://localhost:27017"

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DB_NAME = "adaptive_math_db"

def get_db():
    """Returns the database connection."""
    client = pymongo.MongoClient(MONGO_URI)
    return client[DB_NAME]
