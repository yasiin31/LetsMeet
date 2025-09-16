'''

Install pymongo: py -m pip install pymongo
Install pg8000: py -m pip install pg8000

Use py ./scripts/transform_excel.py in the LetsMeet folder!!!
For example: /LetsMeet> py ./scripts/transform_excel.py

'''

from pymongo import MongoClient
import pg8000
from datetime import datetime
from validationTabel.validation_tabel import valiTabel

valiTabel()

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

count_users, count_friendships, count_likes, count_msgs = 0, 0, 0, 0

for doc in collection.find():
    email = doc['_id']

    name = doc.get('name', '')
    name_parts = name.split(', ')
    if len(name_parts) == 2:
        last_name, first_name = name_parts
    else:
        first_name = name
        last_name = ''

    phone = doc.get('phone', '')

    birth_date = None
    gender = None
    interested_in = None
    city_id = None

    created_at = datetime.fromisoformat(doc.get('createdAt').replace('Z', '+00:00'))
    updated_at = datetime.fromisoformat(doc.get('updatedAt').replace('Z', '+00:00'))

    cursor.execute("""
                   INSERT INTO users (first_name, last_name, email, phone_number,
                                      birth_date, gender, interested_in, city_id,
                                      created_at, updated_at)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s) ON CONFLICT (email) DO
                   UPDATE SET
                       first_name = EXCLUDED.first_name,
                       last_name = EXCLUDED.last_name,
                       phone_number = EXCLUDED.phone_number,
                       updated_at = EXCLUDED.updated_at
                       RETURNING user_id
                   """, (first_name, last_name, email, phone, birth_date, gender,
                         interested_in, city_id, created_at, updated_at))
    count_users += 1


conn.commit()
print(f"[OK] {count_users} Benutzer übertragen.")

for doc in collection.find():
    email = doc['_id']

    cursor.execute("SELECT user_id FROM users WHERE email = %s", (email,))
    result = cursor.fetchone()
    if not result:
        continue

    user_id = result[0]

    for like in doc.get('likes', []):
        cursor.execute("SELECT user_id FROM users WHERE email = %s", (like['liked_email'],))
        liked_user_result = cursor.fetchone()

        if liked_user_result:
            liked_id = liked_user_result[0]
            like_time = datetime.fromisoformat(like['timestamp'].replace('Z', '+00:00'))

            cursor.execute("""
                           INSERT INTO likes (liker_id, liked_id, status, created_at)
                           VALUES (%s, %s, %s, %s)
                           """, (user_id, liked_id, like['status'], like_time))
            count_likes += 1

    for msg in doc.get('messages', []):
        cursor.execute("SELECT user_id FROM users WHERE email = %s", (msg['receiver_email'],))
        receiver_result = cursor.fetchone()

        if receiver_result:
            receiver_id = receiver_result[0]
            msg_time = datetime.fromisoformat(msg['timestamp'].replace('Z', '+00:00'))

            cursor.execute("""
                           INSERT INTO messages (sender_id, receiver_id, conversation_id, message, sent_at)
                           VALUES (%s, %s, %s, %s, %s)
                           """, (user_id, receiver_id, msg['conversation_id'], msg['message'], msg_time))
            count_msgs += 1

conn.commit()

print(f"[OK] {count_friendships} Freundschaften übertragen.")
print(f"[OK] {count_likes} Likes übertragen.")
print(f"[OK] {count_msgs} Nachrichten übertragen.")

cursor.close()
conn.close()
print("[DONE] Migration abgeschlossen.")
