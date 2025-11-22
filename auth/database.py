import os
from pymongo import MongoClient

# Get MONGO_URI from environment (Render or local .env)
MONGO_URI = os.getenv("MONGO_URI")

# Connect to Atlas
client = MongoClient(MONGO_URI)

# Database name (you choose)
db = client["meeting_app"]

# Collections
users_collection = db["users"]
