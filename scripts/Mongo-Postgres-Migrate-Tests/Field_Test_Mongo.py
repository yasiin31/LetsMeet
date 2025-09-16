import pg8000
from pymongo import MongoClient
from datetime import datetime

print("=== FIELD TEST FÜR TRANSFORM_MONGODB.PY ===\n")

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

test_results = {
    'users': {'passed': 0, 'failed': 0, 'details': []},
    'likes': {'passed': 0, 'failed': 0, 'details': []},
    'messages': {'passed': 0, 'failed': 0, 'details': []}
}

print("=== Prüfe Users ===")

cursor.execute("SELECT email, first_name, last_name, phone_number, created_at FROM users")
pg_users = {row[0]: row[1:] for row in cursor.fetchall()}

for doc in mongo_collection.find():
    # Mongo Felder
    email = doc["_id"]
if email in pg_users:
    pg_data = pg_users[email]

    # Parse name from MongoDB
    name = doc.get('name', '')
    name_parts = name.split(', ')
    if len(name_parts) == 2:
        mongo_last_name, mongo_first_name = name_parts
    else:
        mongo_first_name = name
        mongo_last_name = ''

    # Compare fields
    if (pg_data[0] == mongo_first_name and
            pg_data[1] == mongo_last_name and
            pg_data[2] == doc.get('phone', '')):

        # Test timestamp conversion
        mongo_created_at = datetime.fromisoformat(doc.get('createdAt').replace('Z', '+00:00'))
        if abs((pg_data[3] - mongo_created_at).total_seconds()) < 1:  # Allow 1 second difference
            test_results['users']['passed'] += 1
        else:
            test_results['users']['failed'] += 1
            test_results['users']['details'].append(
                f"Timestamp mismatch for {email}: MongoDB={mongo_created_at}, PostgreSQL={pg_data[3]}"
            )
    else:
        test_results['users']['failed'] += 1
        test_results['users']['details'].append(
            f"Field mismatch for {email}: MongoDB(name={name}, phone={doc.get('phone', '')}) vs "
            f"PostgreSQL(first={pg_data[0]}, last={pg_data[1]}, phone={pg_data[2]})"
        )
else:
    test_results['users']['failed'] += 1
    test_results['users']['details'].append(f"User {email} not found in PostgreSQL")

    # Test 2: Likes data integrity
print("=== Prüfe Likes ===")
cursor.execute("""
               SELECT u.email, u2.email, l.status, l.created_at
               FROM likes l
                        JOIN users u ON l.liker_id = u.user_id
                        JOIN users u2 ON l.liked_id = u2.user_id
               """)

for liker_email, liked_email, status, created_at in cursor.fetchall():
    # Find the corresponding like in MongoDB
    found = False
    for mongo_doc in mongo_collection.find():
        if mongo_doc['_id'] == liker_email:
            for like in mongo_doc.get('likes', []):
                if like['liked_email'] == liked_email:
                    mongo_time = datetime.fromisoformat(like['timestamp'].replace('Z', '+00:00'))
                    if (like['status'] == status and
                            abs((created_at - mongo_time).total_seconds()) < 1):
                        test_results['likes']['passed'] += 1
                    else:
                        test_results['likes']['failed'] += 1
                        test_results['likes']['details'].append(
                            f"Like mismatch: {liker_email}->{liked_email}, "
                            f"Status: MongoDB={like['status']}, PostgreSQL={status}, "
                            f"Time diff: {(created_at - mongo_time).total_seconds()}s"
                        )
                    found = True
                    break
            if found:
                break

    if not found:
        test_results['likes']['failed'] += 1
        test_results['likes']['details'].append(
            f"Like nicht gefunden in MongoDB: {liker_email}->{liked_email}"
        )

# Test 3: Messages data integrity
print("=== Prüfe Messages ===")
cursor.execute("""
               SELECT u.email, u2.email, m.conversation_id, m.message, m.sent_at
               FROM messages m
                        JOIN users u ON m.sender_id = u.user_id
                        JOIN users u2 ON m.receiver_id = u2.user_id
               """)

for sender_email, receiver_email, conv_id, message, sent_at in cursor.fetchall():
    found = False
    for mongo_doc in mongo_collection.find():
        if mongo_doc['_id'] == sender_email:
            for msg in mongo_doc.get('messages', []):
                if (msg['receiver_email'] == receiver_email and
                        msg['conversation_id'] == conv_id and
                        msg['message'] == message):

                    mongo_time = datetime.fromisoformat(msg['timestamp'].replace('Z', '+00:00'))
                    if abs((sent_at - mongo_time).total_seconds()) < 1:
                        test_results['messages']['passed'] += 1
                    else:
                        test_results['messages']['failed'] += 1
                        test_results['messages']['details'].append(
                            f"Message time mismatch: {sender_email}->{receiver_email}, "
                            f"Time diff: {(sent_at - mongo_time).total_seconds()}s"
                        )
                    found = True
                    break
            if found:
                break

    if not found:
        test_results['messages']['failed'] += 1
        test_results['messages']['details'].append(
            f"Message nicht gefunden in MongoDB: {sender_email}->{receiver_email}, conv_id={conv_id}"
        )

# Print results
print("\n=== FIELD TEST RESULTS ===")
for table, results in test_results.items():
    total = results['passed'] + results['failed']
    if total > 0:
        success_rate = (results['passed'] / total) * 100
    else:
        success_rate = 0

    print(f"{table.upper()}: {results['passed']}/{total} passed ({success_rate:.1f}%)")

    if results['failed'] > 0 and results['details']:
        print(f"  Failed details (first 5):")
        for detail in results['details'][:5]:
            print(f"    - {detail}")

cursor.close()
conn.close()
client.close()

print("\n[ALLES GETESTET] Vollabgleich abgeschlossen.")
