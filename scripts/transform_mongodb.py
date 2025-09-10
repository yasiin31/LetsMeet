from pymongo import MongoClient
import pg8000
from datetime import datetime

# MongoDB Verbindung 
client = MongoClient("mongodb://localhost:27018/")
db = client["LetsMeet"]
collection = db["users"]
print("[OK] Verbindung zu MongoDB aufgebaut.")

#PostgreSQL Verbindung
conn = pg8000.connect(
    host='localhost',
    database='lf8_lets_meet_db',
    user='user',
    password='secret',
    port=5433
)
cursor = conn.cursor()
print("[OK] Verbindung zu PostgreSQL hergestellt.")

# Tabellen erstellen
cursor.execute("""
CREATE TABLE IF NOT EXISTS city (
    city_id SERIAL PRIMARY KEY,
    name TEXT,
    zip_code TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS hobby (
    hobby_id SERIAL PRIMARY KEY,
    name TEXT UNIQUE
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id TEXT PRIMARY KEY,
    first_name TEXT,
    last_name TEXT,
    email TEXT UNIQUE,
    phone_number TEXT,
    birth_date DATE,
    gender TEXT,
    interested_in TEXT,
    city_id INT REFERENCES city(city_id),
    created_at TIMESTAMP,
    updated_at TIMESTAMP
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS user_hobby (
    user_id TEXT REFERENCES users(user_id),
    hobby_id INT REFERENCES hobby(hobby_id),
    PRIMARY KEY (user_id, hobby_id)
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS friendship (
    user_one_id TEXT REFERENCES users(user_id),
    user_two_id TEXT REFERENCES users(user_id),
    created_at TIMESTAMP,
    PRIMARY KEY (user_one_id, user_two_id)
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS likes (
    like_id SERIAL PRIMARY KEY,
    liker_id TEXT REFERENCES users(user_id),
    liked_id TEXT,
    status TEXT,
    created_at TIMESTAMP
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS messages (
    message_id SERIAL PRIMARY KEY,
    sender_id TEXT REFERENCES users(user_id),
    receiver_id TEXT,
    conversation_id INT,
    message TEXT,
    sent_at TIMESTAMP
)
""")
print("[OK] Tabellen erstellt oder existieren bereits.")

# === Migration starten ===
count_users, count_friendships, count_likes, count_msgs = 0, 0, 0, 0

for doc in collection.find():
    user_id = str(doc["_id"])        # Mongo _id = E-Mail
    email = str(doc["_id"])
    phone = doc.get("phone")

    # Namen aufsplitten (Format: "Nachname, Vorname")
    full_name = doc.get("name")
    first_name, last_name = None, None
    if full_name and "," in full_name:
        last_name, first_name = [x.strip() for x in full_name.split(",", 1)]
    elif full_name:
        parts = full_name.split(" ")
        first_name, last_name = parts[0], " ".join(parts[1:])

    # Zeitstempel
    created_at = datetime.fromisoformat(doc.get("createdAt")) if doc.get("createdAt") else None
    updated_at = datetime.fromisoformat(doc.get("updatedAt")) if doc.get("updatedAt") else None

    # User einfügen (fehlende Felder = NULL)
    cursor.execute("""
        INSERT INTO users (user_id, first_name, last_name, email, phone_number,
                           birth_date, gender, interested_in, city_id, created_at, updated_at)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        ON CONFLICT (user_id) DO NOTHING
    """, (user_id, first_name, last_name, email, phone,
          None, None, None, None, created_at, updated_at))
    count_users += 1

    # Freundschaften
    for friend_id in doc.get("friends", []):
        cursor.execute("""
            INSERT INTO friendship (user_one_id, user_two_id, created_at)
            VALUES (%s,%s,%s)
            ON CONFLICT DO NOTHING
        """, (user_id, friend_id, datetime.utcnow()))
        count_friendships += 1

    # Likes
    for like in doc.get("likes", []):
        liker = user_id
        liked = like.get("liked_email")
        status = like.get("status")
        ts = datetime.strptime(like.get("timestamp"), "%Y-%m-%d %H:%M:%S")
        cursor.execute("""
            INSERT INTO likes (liker_id, liked_id, status, created_at)
            VALUES (%s,%s,%s,%s)
        """, (liker, liked, status, ts))
        count_likes += 1

    # Messages
    for msg in doc.get("messages", []):
        receiver = msg.get("receiver_email")
        conversation_id = msg.get("conversation_id")
        message = msg.get("message")
        ts = datetime.strptime(msg.get("timestamp"), "%Y-%m-%d %H:%M:%S")
        cursor.execute("""
            INSERT INTO messages (sender_id, receiver_id, conversation_id, message, sent_at)
            VALUES (%s,%s,%s,%s,%s)
        """, (user_id, receiver, conversation_id, message, ts))
        count_msgs += 1

conn.commit()

print(f"[OK] {count_users} Benutzer übertragen.")
print(f"[OK] {count_friendships} Freundschaften übertragen.")
print(f"[OK] {count_likes} Likes übertragen.")
print(f"[OK] {count_msgs} Nachrichten übertragen.")

cursor.close()
conn.close()
print("[DONE] Migration abgeschlossen.")
