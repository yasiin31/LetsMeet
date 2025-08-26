from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27018/")

db = client["LetsMeet"]

collection = db["users"]

for doc in collection.find():
    print(doc)