from pymongo import MongoClient
import os
MONGO_URI = os.getenv("MONGO_URI")
client = MongoClient(MONGO_URI)

db = client["ecommerce_db"]

orders_collection = db["orders_db"]