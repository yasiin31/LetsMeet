'''
Master-Skript zum Count-Testen aller Transform-Skripte
Verwendung: py ./scripts/General/Count_Test_Big.py im LetsMeet-Ordner
'''


import pandas as pd
import pg8000
import re
import sys
import os
import xml.etree.ElementTree as ET
from pymongo import MongoClient

# PostgreSQL Verbindung
conn = pg8000.connect(
    host='localhost',
    database='lf8_lets_meet_db',
    user='user',
    password='secret',
    port=5433
)
cursor = conn.cursor()
print("[OK] Verbindung zu PostgreSQL hergestellt.")

# MongoDB Verbindung
mongo_client = MongoClient("mongodb://localhost:27018/")
mongo_db = mongo_client["LetsMeet"]
mongo_collection = mongo_db["users"]
print("[OK] Verbindung zu MongoDB hergestellt.")

# Funktion zur Adressverarbeitung (wie in transform_excel.py)
def process_address(address_string):
    if pd.isna(address_string):
        return None, None, None

    parts = str(address_string).split(',')
    if len(parts) < 2:
        return None, None, None

    street = parts[0].strip()

    if len(parts) >= 3:
        # Format: "Straße, PLZ, Ort"
        zip_code = parts[1].strip()
        city_name = parts[2].strip()
    else:
        # Format: "Straße, PLZ Ort" - wir müssen PLZ und Ort trennen
        location_parts = parts[1].strip().split(' ')
        if len(location_parts) >= 2:
            zip_code = location_parts[0]
            city_name = ' '.join(location_parts[1:])
        else:
            zip_code = None
            city_name = None

    return street, zip_code, city_name

# 1. EXCEL-DATEI TEST
print("\n" + "="*50)
print("EXCEL-DATEI TEST")
print("="*50)

excel_file = "Lets Meet DB Dump.xlsx"
df = pd.read_excel(excel_file)
print(f"[OK] Excel-Datei eingelesen: {len(df)} Einträge gefunden")

# Count aus Excel-Datei
excel_user_count = len(df)
excel_hobby_entries = 0
unique_cities = set()  # Für einzigartige Stadt/PLZ-Kombinationen

# Hobby- und City-Zählung aus Excel
for index, row in df.iterrows():
    # Hobbies zählen
    hobby_string = row.iloc[3] if len(row) > 3 else ''
    if not pd.isna(hobby_string):
        hobbies = str(hobby_string).split(';')
        excel_hobby_entries += len([h for h in hobbies if h.strip()])

    # EINZIGARTIGE Cities zählen (wie in der Datenbank)
    address = row.iloc[1] if len(row) > 1 else ''
    if not pd.isna(address):
        street, zip_code, city_name = process_address(address)
        if city_name and zip_code:
            city_key = f"{zip_code}_{city_name}".lower().strip()
            unique_cities.add(city_key)

excel_city_entries = len(unique_cities)

# Count aus PostgreSQL-Datenbank für Excel-Daten
cursor.execute("SELECT COUNT(*) FROM users")
pg_user_count = cursor.fetchone()[0]

cursor.execute("SELECT COUNT(*) FROM user_hobby")
pg_hobby_count = cursor.fetchone()[0]

cursor.execute("SELECT COUNT(*) FROM city")
pg_city_count = cursor.fetchone()[0]

# Print Excel results
print("COUNT COMPARISON EXCEL TRANSFORMATION:")
print(f"Users:     Excel={excel_user_count}, PostgreSQL={pg_user_count}, Match={excel_user_count == pg_user_count}")
print(f"Hobbies:   Excel={excel_hobby_entries}, PostgreSQL={pg_hobby_count}, Match={excel_hobby_entries == pg_hobby_count}")
print(f"Cities:    Excel={excel_city_entries}, PostgreSQL={pg_city_count}, Match={excel_city_entries == pg_city_count}")

# 2. MONGODB TEST
print("\n" + "="*50)
print("MONGODB TEST")
print("="*50)

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

# Count friendships
cursor.execute("SELECT COUNT(*) FROM friendship")
pg_friendship_count = cursor.fetchone()[0]

# Print MongoDB results
print("COUNT COMPARISON MONGODB TRANSFORMATION:")
print(f"Users:     MongoDB={mongo_user_count}, PostgreSQL={pg_user_count}, Match={mongo_user_count == pg_user_count}")
print(f"Likes:     MongoDB={mongo_like_count}, PostgreSQL={pg_like_count}, Match={mongo_like_count == pg_like_count}")
print(f"Messages:  MongoDB={mongo_message_count}, PostgreSQL={pg_message_count}, Match={mongo_message_count == pg_message_count}")
print(f"Friendships: PostgreSQL={pg_friendship_count} (MongoDB source not implemented)")

# 3. XML TEST
print("\n" + "="*50)
print("XML TEST")
print("="*50)

# XML-Datei einlesen und zählen
xml_file_path = "Lets_Meet_Hobbies.xml"
tree = ET.parse(xml_file_path)
root = tree.getroot()

# Count users in XML
xml_user_count = len(root.findall('user'))

# Count hobbies in XML
xml_hobby_count = 0
xml_user_hobby_count = 0

for user_elem in root.findall('user'):
    # Hobbies aus <hobby> Elementen
    for hobby_elem in user_elem.findall('hobby'):
        if hobby_elem.text is not None and hobby_elem.text.strip():
            xml_hobby_count += 1
            xml_user_hobby_count += 1

    # Hobbies aus <hobbies> Container
    hobbies_elem = user_elem.find('hobbies')
    if hobbies_elem is not None:
        for hobby_elem in hobbies_elem.findall('hobby'):
            if hobby_elem.text is not None and hobby_elem.text.strip():
                xml_hobby_count += 1
                xml_user_hobby_count += 1

# Count in PostgreSQL für XML-Daten
cursor.execute("SELECT COUNT(*) FROM hobby")
pg_hobby_count = cursor.fetchone()[0]

cursor.execute("SELECT COUNT(*) FROM user_hobby")
pg_user_hobby_count = cursor.fetchone()[0]

# Print XML results
print("COUNT COMPARISON XML IMPORT:")
print(f"Users:        XML={xml_user_count}, PostgreSQL={pg_user_count}, Match={xml_user_count == pg_user_count}")
print(f"Hobbies:      XML={xml_hobby_count}, PostgreSQL={pg_hobby_count}, Match={xml_hobby_count == pg_hobby_count}")
print(f"User-Hobbies: XML={xml_user_hobby_count}, PostgreSQL={pg_user_hobby_count}, Match={xml_user_hobby_count == pg_user_hobby_count}")

# 4. GESAMTTEST AUSWERTUNG
print("\n" + "="*50)
print("GESAMTTEST AUSWERTUNG")
print("="*50)

# Test-Ergebnisse sammeln
test_results = []

# Excel Tests
test_results.append(("Excel Users", excel_user_count == pg_user_count))
test_results.append(("Excel Hobbies", excel_hobby_entries == pg_hobby_count))
test_results.append(("Excel Cities", excel_city_entries == pg_city_count))

# MongoDB Tests
test_results.append(("MongoDB Users", mongo_user_count == pg_user_count))
test_results.append(("MongoDB Likes", mongo_like_count == pg_like_count))
test_results.append(("MongoDB Messages", mongo_message_count == pg_message_count))

# XML Tests
test_results.append(("XML Users", xml_user_count == pg_user_count))
test_results.append(("XML Hobbies", xml_hobby_count == pg_hobby_count))
test_results.append(("XML User-Hobbies", xml_user_hobby_count == pg_user_hobby_count))

# Gesamtstatistik berechnen
total_tests = len(test_results)
passed_tests = sum(1 for _, result in test_results if result)
success_rate = (passed_tests / total_tests) * 100

# Ergebnisse anzeigen
print(f"GESAMTERGEBNIS: {passed_tests}/{total_tests} Tests bestanden ({success_rate:.1f}%)")
print("\nDETAILS:")
for test_name, result in test_results:
    status = "✅" if result else "❌"
    print(f"  {status} {test_name}")

if passed_tests == total_tests:
    print("\n🎉 ALLE TESTS BESTANDEN! Die Datenbank ist konsistent.")
else:
    print(f"\n⚠️  {total_tests - passed_tests} Tests fehlgeschlagen.")

# Verbindungen schließen
cursor.close()
conn.close()
mongo_client.close()
print("\n[DONE] Kombinierter Count-Test abgeschlossen.")