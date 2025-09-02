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
