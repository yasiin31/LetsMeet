import pg8000
from pymongo import MongoClient

# MongoDB 
client = MongoClient("mongodb://localhost:27018/")
mongo_db = client["LetsMeet"]
mongo_collection = mongo_db["users"]

# Postgres 
conn = pg8000.connect(
    host='localhost',
    database='lf8_lets_meet_db',
    user='user',
    password='secret',
    port=5433
)
cursor = conn.cursor()

# Users count
mongo_users = mongo_collection.count_documents({})
cursor.execute("SELECT COUNT(*) FROM users;")
pg_users = cursor.fetchone()[0]

if pg_users == mongo_users:
    print(f"[OK] Users count matches: {pg_users}")
else:
    print(f"[ERROR] Users count mismatch. Mongo: {mongo_users}, Postgres: {pg_users}")

# Likes count
mongo_likes = sum(len(doc.get("likes", [])) for doc in mongo_collection.find())
cursor.execute("SELECT COUNT(*) FROM likes;")
pg_likes = cursor.fetchone()[0]

if pg_likes == mongo_likes:
    print(f"[OK] Likes count matches: {pg_likes}")
else:
    print(f"[ERROR] Likes count mismatch. Mongo: {mongo_likes}, Postgres: {pg_likes}")

# Messages count
mongo_msgs = sum(len(doc.get("messages", [])) for doc in mongo_collection.find())
cursor.execute("SELECT COUNT(*) FROM messages;")
pg_msgs = cursor.fetchone()[0]

if pg_msgs == mongo_msgs:
    print(f"[OK] Messages count matches: {pg_msgs}")
else:
    print(f"[ERROR] Messages count mismatch. Mongo: {mongo_msgs}, Postgres: {pg_msgs}")

cursor.close()
conn.close()