from pymongo import MongoClient
import pg8000
from datetime import datetime


client = MongoClient("mongodb://localhost:27018/")
db = client["LetsMeet"]
collection = db["users"]
print("[OK] Verbindung zu MongoDB aufgebaut.")


conn = pg8000.connect(
    host='localhost',
    database='lf8_lets_meet_db',
    user='user',
    password='secret',
    port=5433
)
cursor = conn.cursor()
print("[OK] Verbindung zu PostgreSQL hergestellt.")


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
print("[OK] Tabelle 'users' erstellt oder existiert bereits.")

cursor.execute("""
CREATE TABLE IF NOT EXISTS likes (
    user_id TEXT REFERENCES users(id),
    liked_email TEXT,
    status TEXT,
    timestamp TIMESTAMP
)
""")
print("[OK] Tabelle 'likes' erstellt oder existiert bereits.")

cursor.execute("""
CREATE TABLE IF NOT EXISTS messages (
    user_id TEXT REFERENCES users(id),
    conversation_id INT,
    receiver_email TEXT,
    message TEXT,
    timestamp TIMESTAMP
)
""")
print("[OK] Tabelle 'messages' erstellt oder existiert bereits.")

count_users = 0
count_likes = 0
count_msgs = 0

for doc in collection.find():
    user_id = doc['_id']
    name = doc.get('name')
    phone = doc.get('phone')
    friends = doc.get('friends', [])
    created_at = datetime.fromisoformat(doc.get('createdAt'))
    updated_at = datetime.fromisoformat(doc.get('updatedAt'))

    cursor.execute("""
        INSERT INTO users (id, name, phone, friends, created_at, updated_at)
        VALUES (%s, %s, %s, %s, %s, %s)
        ON CONFLICT (id) DO NOTHING
    """, (user_id, name, phone, friends, created_at, updated_at))
    count_users += 1

    for like in doc.get('likes', []):
        like_time = datetime.fromisoformat(like['timestamp'])
        cursor.execute("""
            INSERT INTO likes (user_id, liked_email, status, timestamp)
            VALUES (%s, %s, %s, %s)
        """, (user_id, like['liked_email'], like['status'], like_time))
        count_likes += 1

    for msg in doc.get('messages', []):
        msg_time = datetime.fromisoformat(msg['timestamp'])
        cursor.execute("""
            INSERT INTO messages (user_id, conversation_id, receiver_email, message, timestamp)
            VALUES (%s, %s, %s, %s, %s)
        """, (user_id, msg['conversation_id'], msg['receiver_email'], msg['message'], msg_time))
        count_msgs += 1

conn.commit()
print(f"[OK] {count_users} Benutzer übertragen.")
print(f"[OK] {count_likes} Likes übertragen.")
print(f"[OK] {count_msgs} Nachrichten übertragen.")

cursor.close()
conn.close()
print("[DONE] Migration abgeschlossen.")
