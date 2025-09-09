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


cursor = conn.cursor()