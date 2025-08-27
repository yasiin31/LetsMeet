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
    port=5432
)
cursor = conn.cursor()

