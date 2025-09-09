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

print("=== Prüfe Users ===")
for doc in mongo_collection.find():
    cursor.execute("SELECT name, phone FROM users WHERE id=%s", (doc["_id"],))
    result = cursor.fetchone()
    if not result:
        print(f"[FEHLER] User {doc['_id']} fehlt in Postgres!")
        continue
    pg_name, pg_phone = result
    if pg_name != doc.get("name") or pg_phone != doc.get("phone"):
        print(f"[FEHLER] User {doc['_id']} stimmt nicht überein!")
print("[TEST Users abgeschlossen]")

print("\n=== Prüfe Likes ===")
for doc in mongo_collection.find():
    for like in doc.get("likes", []):
        cursor.execute("""
            SELECT liked_email, status FROM likes 
            WHERE user_id=%s AND liked_email=%s
        """, (doc["_id"], like["liked_email"]))
        result = cursor.fetchone()
        if not result:
            print(f"[FEHLER] Like von {doc['_id']} zu {like['liked_email']} fehlt in Postgres!")
            continue
        pg_email, pg_status = result
        if pg_email != like["liked_email"] or pg_status != like["status"]:
            print(f"[FEHLER] Like von {doc['_id']} zu {like['liked_email']} stimmt nicht überein!")
print("[TEST Likes abgeschlossen]")


cursor = conn.cursor()