from __future__ import annotations

from pymongo import MongoClient
from pymongo.collection import Collection

MONGO_URI = "mongodb://localhost:27017"
DB_NAME = "meeting_app"
USERS_COLLECTION = "users"

client = MongoClient(MONGO_URI)
db = client[DB_NAME]
users_collection: Collection = db[USERS_COLLECTION]

# Ensure email uniqueness for fast lookups
users_collection.create_index("email", unique=True)
