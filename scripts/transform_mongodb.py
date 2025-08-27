from pymongo import MongoClient
import pg8000

#Mongo DB Verbindung 
client = MongoClient("mongodb://localhost:27018/")
db = client["LetsMeet"]
collection = db["users"]

for doc in collection.find():
    data = doc

conn = pg8000.connect(
    host='localhost',
    database='lf8_lets_meet_db',
    user='user',
    password='secret',
    port=5433
)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    name TEXT,
    phone TEXT,
    friends TEXT[],
    created_at TIMESTAMP,
    updated_at TIMESTAMP
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS likes (
    user_id TEXT REFERENCES users(id),
    liked_email TEXT,
    status TEXT,
    timestamp TIMESTAMP
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS messages (
    user_id TEXT REFERENCES users(id),
    conversation_id INT,
    receiver_email TEXT,
    message TEXT,
    timestamp TIMESTAMP
)
""")

conn.commit()
cursor.close()
conn.close()