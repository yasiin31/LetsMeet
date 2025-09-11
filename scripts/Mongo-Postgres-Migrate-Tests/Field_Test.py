import pg8000
from pymongo import MongoClient

# MongoDB
client = MongoClient("mongodb://localhost:27018/")
mongo_db = client["LetsMeet"]
mongo_collection = mongo_db["users"]

# Postgres
conn = pg8000.connect(
    host="localhost",
    database="lf8_lets_meet_db",
    user="user",
    password="secret",
    port=5433
)
cursor = conn.cursor()


print("=== Prüfe Users ===")
for doc in mongo_collection.find():
    # Mongo Felder
    email = doc["_id"]
    full_name = doc.get("name", "")
    phone = doc.get("phone")

    if "," in full_name:
        last_name, first_name = [part.strip() for part in full_name.split(",", 1)]
    else:
        first_name, last_name = full_name, ""

    cursor.execute("""
        SELECT first_name, last_name, email, phone_number
        FROM users WHERE email=%s
    """, (email,))
    result = cursor.fetchone()
    if not result:
        print(f"[FEHLER] User {email} fehlt in Postgres!")
        continue

    pg_first, pg_last, pg_email, pg_phone = result
    if pg_first != first_name or pg_last != last_name or pg_email != email or pg_phone != phone:
        print(f"[FEHLER] User {email} stimmt nicht überein!")
print("[TEST Users abgeschlossen]")



print("\n=== Prüfe Likes ===")
for doc in mongo_collection.find():
    liker_email = doc["_id"]


    cursor.execute("SELECT user_id FROM users WHERE email=%s", (liker_email,))
    liker = cursor.fetchone()
    if not liker:
        continue
    liker_id = liker[0]

    for like in doc.get("likes", []):
        liked_email = like["liked_email"]


        cursor.execute("SELECT user_id FROM users WHERE email=%s", (liked_email,))
        liked = cursor.fetchone()
        if not liked:
            print(f"[FEHLER] Liked-User {liked_email} fehlt in Postgres!")
            continue
        liked_id = liked[0]

        cursor.execute("""
            SELECT status FROM likes 
            WHERE liker_id=%s AND liked_id=%s
        """, (liker_id, liked_id))
        result = cursor.fetchone()
        if not result:
            print(f"[FEHLER] Like von {liker_email} → {liked_email} fehlt in Postgres!")
            continue
        pg_status = result[0]
        if pg_status != like["status"]:
            print(f"[FEHLER] Like von {liker_email} → {liked_email} stimmt nicht überein!")
print("[TEST Likes abgeschlossen]")



print("\n=== Prüfe Messages ===")
for doc in mongo_collection.find():
    sender_email = doc["_id"]


    cursor.execute("SELECT user_id FROM users WHERE email=%s", (sender_email,))
    sender = cursor.fetchone()
    if not sender:
        continue
    sender_id = sender[0]

    for msg in doc.get("messages", []):
        receiver_email = msg["receiver_email"]

       
        cursor.execute("SELECT user_id FROM users WHERE email=%s", (receiver_email,))
        receiver = cursor.fetchone()
        if not receiver:
            print(f"[FEHLER] Receiver {receiver_email} fehlt in Postgres!")
            continue
        receiver_id = receiver[0]

        cursor.execute("""
            SELECT message FROM messages
            WHERE sender_id=%s AND receiver_id=%s AND conversation_id=%s
        """, (sender_id, receiver_id, msg["conversation_id"]))
        result = cursor.fetchone()
        if not result:
            print(f"[FEHLER] Message von {sender_email} an {receiver_email} fehlt (Conv {msg['conversation_id']})!")
            continue
        pg_message = result[0]
        if pg_message != msg["message"]:
            print(f"[FEHLER] Message von {sender_email} an {receiver_email} stimmt nicht (Conv {msg['conversation_id']})!")
print("[TEST Messages abgeschlossen]")



cursor.close()
conn.close()
print("\n[ALLES GETESTET] Vollabgleich abgeschlossen.")
