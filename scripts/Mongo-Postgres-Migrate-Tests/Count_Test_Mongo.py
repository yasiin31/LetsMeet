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

# Count users
cursor.execute("SELECT COUNT(*) FROM users")
pg_user_count = cursor.fetchone()[0]
mongo_user_count = mongo_collection.count_documents({})

# Count likes
cursor.execute("SELECT COUNT(*) FROM likes")
pg_like_count = cursor.fetchone()[0]
mongo_like_count = sum(len(doc.get('likes', [])) for doc in mongo_collection.find())

# Count messages
cursor.execute("SELECT COUNT(*) FROM messages")
pg_message_count = cursor.fetchone()[0]
mongo_message_count = sum(len(doc.get('messages', [])) for doc in mongo_collection.find())

# Count friendships (if implemented)
cursor.execute("SELECT COUNT(*) FROM friendship")
pg_friendship_count = cursor.fetchone()[0]

# Print results
print("COUNT COMPARISON:")
print(f"Users:     MongoDB={mongo_user_count}, PostgreSQL={pg_user_count}, Match={mongo_user_count == pg_user_count}")
print(f"Likes:     MongoDB={mongo_like_count}, PostgreSQL={pg_like_count}, Match={mongo_like_count == pg_like_count}")
print(f"Messages:  MongoDB={mongo_message_count}, PostgreSQL={pg_message_count}, Match={mongo_message_count == pg_message_count}")
print(f"Friendships: PostgreSQL={pg_friendship_count} (MongoDB source not implemented)")

# Calculate success rates
user_match = mongo_user_count == pg_user_count
like_match = mongo_like_count == pg_like_count
message_match = mongo_message_count == pg_message_count

total_tests = 3
passed_tests = sum([user_match, like_match, message_match])
success_rate = (passed_tests / total_tests) * 100

print(f"\nOVERALL: {passed_tests}/{total_tests} tests passed ({success_rate:.1f}%)")

if not user_match:
    print("  ❌ User count mismatch!")
if not like_match:
    print("  ❌ Like count mismatch!")
if not message_match:
    print("  ❌ Message count mismatch!")

if user_match and like_match and message_match:
    print("  ✅ All count tests passed!")

cursor.close()
conn.close()
client.close()