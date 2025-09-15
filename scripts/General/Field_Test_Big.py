'''
Master-Skript zum Felder-Testen aller Transform-Skripte
Verwendung: py ./scripts/General/Field_Test_Big.py im LetsMeet-Ordner
'''

import pg8000
from pymongo import MongoClient
import xml.etree.ElementTree as ET
import pandas as pd
import re
from datetime import datetime
import sys
import os

# Füge den Pfad hinzu, um transform_excel Funktionen zu importieren
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from transform_excel import extract_hobbies, process_address, normalize_gender, normalize_interests, process_birthdate

print("=== KOMPLETTER FIELD TEST FÜR ALLE TRANSFORMATIONEN ===\n")

# PostgreSQL Verbindung
conn = pg8000.connect(
    host='localhost',
    database='lf8_lets_meet_db',
    user='user',
    password='secret',
    port=5433
)
cursor = conn.cursor()
print("[OK] Verbindung zu PostgreSQL erfolgreich hergestellt")

# MongoDB Verbindung
mongo_client = MongoClient("mongodb://localhost:27018/")
mongo_db = mongo_client["LetsMeet"]
mongo_collection = mongo_db["users"]
print("[OK] Verbindung zu MongoDB erfolgreich hergestellt")

# Test-Ergebnisse
test_results = {
    'users': {'passed': 0, 'failed': 0, 'details': []},
    'hobbies': {'passed': 0, 'failed': 0, 'details': []},
    'cities': {'passed': 0, 'failed': 0, 'details': []},
    'likes': {'passed': 0, 'failed': 0, 'details': []},
    'messages': {'passed': 0, 'failed': 0, 'details': []},
    'user_hobbies': {'passed': 0, 'failed': 0, 'details': []}
}

def test_mongodb_users():
    print("=== Prüfe MongoDB Users ===")

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
                if abs((pg_data[3] - mongo_created_at).total_seconds()) < 1:
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

def test_mongodb_likes():
    print("=== Prüfe MongoDB Likes ===")

    cursor.execute("""
                   SELECT u.email, u2.email, l.status, l.created_at
                   FROM likes l
                            JOIN users u ON l.liker_id = u.user_id
                            JOIN users u2 ON l.liked_id = u2.user_id
                   """)

    for liker_email, liked_email, status, created_at in cursor.fetchall():
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

def test_mongodb_messages():
    print("=== Prüfe MongoDB Messages ===")

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

def test_xml_users():
    print("=== Prüfe XML Users ===")

    cursor.execute("SELECT email, first_name, last_name, phone_number, birth_date, gender, interested_in FROM users")
    pg_users = {row[0]: row[1:] for row in cursor.fetchall()}

    xml_file_path = "Lets_Meet_Hobbies.xml"
    tree = ET.parse(xml_file_path)
    root = tree.getroot()

    for user_elem in root.findall('user'):
        email = user_elem.find('email').text if user_elem.find('email') is not None else None

        if not email:
            test_results['users']['failed'] += 1
            test_results['users']['details'].append("User ohne E-Mail gefunden")
            continue

        if email in pg_users:
            pg_data = pg_users[email]

            # XML-Daten extrahieren
            xml_first_name = user_elem.find('first_name').text if user_elem.find('first_name') is not None else ''
            xml_last_name = user_elem.find('last_name').text if user_elem.find('last_name') is not None else ''
            xml_phone = user_elem.find('phone').text if user_elem.find('phone') is not None else ''

            # Vergleiche Felder
            if (pg_data[0] == xml_first_name and
                    pg_data[1] == xml_last_name and
                    pg_data[2] == xml_phone):
                test_results['users']['passed'] += 1
            else:
                test_results['users']['failed'] += 1
                test_results['users']['details'].append(
                    f"Feld-Konflikt für {email}: "
                    f"XML(first={xml_first_name}, last={xml_last_name}, phone={xml_phone}) vs "
                    f"PostgreSQL(first={pg_data[0]}, last={pg_data[1]}, phone={pg_data[2]})"
                )
        else:
            test_results['users']['failed'] += 1
            test_results['users']['details'].append(f"User {email} nicht in PostgreSQL gefunden")

def test_xml_hobbies():
    print("=== Prüfe XML Hobbies ===")

    cursor.execute("SELECT name FROM hobby")
    pg_hobbies = {row[0] for row in cursor.fetchall()}

    xml_file_path = "Lets_Meet_Hobbies.xml"
    tree = ET.parse(xml_file_path)
    root = tree.getroot()

    xml_hobbies = set()
    for user_elem in root.findall('user'):
        hobbies_elem = user_elem.find('hobbies')
        if hobbies_elem is not None:
            for hobby_elem in hobbies_elem.findall('hobby'):
                hobby_name = hobby_elem.text.strip() if hobby_elem.text else ''
                if hobby_name:
                    xml_hobbies.add(hobby_name)

    # Prüfe ob alle Hobbies aus XML in PostgreSQL vorhanden sind
    for hobby in xml_hobbies:
        if hobby in pg_hobbies:
            test_results['hobbies']['passed'] += 1
        else:
            test_results['hobbies']['failed'] += 1
            test_results['hobbies']['details'].append(f"Hobby '{hobby}' nicht in PostgreSQL gefunden")

def test_xml_user_hobbies():
    print("=== Prüfe XML User-Hobby-Verknüpfungen ===")

    cursor.execute("""
                   SELECT u.email, h.name
                   FROM user_hobby uh
                            JOIN users u ON uh.user_id = u.user_id
                            JOIN hobby h ON uh.hobby_id = h.hobby_id
                   """)
    pg_user_hobbies = {}
    for email, hobby_name in cursor.fetchall():
        if email not in pg_user_hobbies:
            pg_user_hobbies[email] = set()
        pg_user_hobbies[email].add(hobby_name)

    xml_file_path = "Lets_Meet_Hobbies.xml"
    tree = ET.parse(xml_file_path)
    root = tree.getroot()

    for user_elem in root.findall('user'):
        email = user_elem.find('email').text if user_elem.find('email') is not None else None
        if not email or email not in pg_user_hobbies:
            continue

        xml_user_hobbies = set()
        hobbies_elem = user_elem.find('hobbies')
        if hobbies_elem is not None:
            for hobby_elem in hobbies_elem.findall('hobby'):
                hobby_name = hobby_elem.text.strip() if hobby_elem.text else ''
                if hobby_name:
                    xml_user_hobbies.add(hobby_name)

        # Vergleiche Hobbies pro User
        if xml_user_hobbies == pg_user_hobbies[email]:
            test_results['user_hobbies']['passed'] += 1
        else:
            test_results['user_hobbies']['failed'] += 1
            missing_in_pg = xml_user_hobbies - pg_user_hobbies[email]
            missing_in_xml = pg_user_hobbies[email] - xml_user_hobbies

            details = f"Hobby-Konflikt für {email}: "
            if missing_in_pg:
                details += f"Fehlt in PostgreSQL: {', '.join(missing_in_pg)}. "
            if missing_in_xml:
                details += f"Fehlt in XML: {', '.join(missing_in_xml)}"

            test_results['user_hobbies']['details'].append(details)

def test_excel_users():
    print("=== Prüfe Excel Users ===")

    cursor.execute("""
                   SELECT email, first_name, last_name, phone_number, birth_date, gender, interested_in, city_id
                   FROM users
                   """)
    pg_users = {row[0]: row[1:] for row in cursor.fetchall()}

    excel_file = "Lets Meet DB Dump.xlsx"
    df = pd.read_excel(excel_file)

    for index, row in df.iterrows():
        # Excel-Daten verarbeiten (wie in transform_excel.py)
        name = row.iloc[0] if len(row) > 0 else ''
        name_parts = name.split(', ')
        if len(name_parts) == 2:
            excel_last_name, excel_first_name = name_parts
        else:
            excel_first_name = name
            excel_last_name = ''

        email = row.iloc[4] if len(row) > 4 else None
        if pd.isna(email):
            continue

        # Verarbeite Adresse
        address = row.iloc[1] if len(row) > 1 else ''
        excel_street, excel_zip_code, excel_city_name = process_address(address)

        # Verarbeite Telefon
        phone = row.iloc[2] if len(row) > 2 else ''
        if pd.isna(phone):
            excel_phone = None
        else:
            excel_phone = re.sub(r'[^0-9+]', '', str(phone))

        # Verarbeite Geschlecht und Interessen
        excel_gender = normalize_gender(row.iloc[5] if len(row) > 5 else '')
        excel_interests = normalize_interests(row.iloc[6] if len(row) > 6 else '')
        excel_birthdate = process_birthdate(row.iloc[7] if len(row) > 7 else '')

        # Vergleiche mit PostgreSQL
        if email in pg_users:
            pg_data = pg_users[email]

            # Vergleiche alle Felder
            if (pg_data[0] == excel_first_name and
                    pg_data[1] == excel_last_name and
                    pg_data[2] == excel_phone and
                    (pg_data[3] == excel_birthdate or (pd.isna(pg_data[3]) and pd.isna(excel_birthdate))) and
                    pg_data[4] == excel_gender and
                    pg_data[5] == excel_interests):

                test_results['users']['passed'] += 1
            else:
                test_results['users']['failed'] += 1
                test_results['users']['details'].append(
                    f"User mismatch for {email}: "
                    f"Excel(first={excel_first_name}, last={excel_last_name}, phone={excel_phone}, "
                    f"birth={excel_birthdate}, gender={excel_gender}, interests={excel_interests}) vs "
                    f"PostgreSQL(first={pg_data[0]}, last={pg_data[1]}, phone={pg_data[2]}, "
                    f"birth={pg_data[3]}, gender={pg_data[4]}, interests={pg_data[5]})"
                )
        else:
            test_results['users']['failed'] += 1
            test_results['users']['details'].append(f"User {email} not found in PostgreSQL")

def test_excel_hobbies():
    print("=== Prüfe Excel Hobbies ===")

    cursor.execute("""
                   SELECT u.email, h.name
                   FROM user_hobby uh
                            JOIN users u ON uh.user_id = u.user_id
                            JOIN hobby h ON uh.hobby_id = h.hobby_id
                   """)
    pg_hobbies = {}
    for email, hobby_name in cursor.fetchall():
        if email not in pg_hobbies:
            pg_hobbies[email] = []
        pg_hobbies[email].append(hobby_name)

    excel_file = "Lets Meet DB Dump.xlsx"
    df = pd.read_excel(excel_file)

    for index, row in df.iterrows():
        email = row.iloc[4] if len(row) > 4 else None
        if pd.isna(email) or email not in pg_hobbies:
            continue

        hobby_string = row.iloc[3] if len(row) > 3 else ''
        excel_hobbies = extract_hobbies(hobby_string)
        pg_user_hobbies = pg_hobbies[email]

        # Vergleiche Hobbies (nur Namen, ohne Priorität)
        excel_hobby_set = set([h[0].lower() for h in excel_hobbies])
        pg_hobby_set = set([h.lower() for h in pg_user_hobbies])

        if excel_hobby_set == pg_hobby_set:
            test_results['hobbies']['passed'] += 1
        else:
            test_results['hobbies']['failed'] += 1
            test_results['hobbies']['details'].append(
                f"Hobby mismatch for {email}: "
                f"Excel={excel_hobby_set} vs PostgreSQL={pg_hobby_set}"
            )

def test_excel_cities():
    print("=== Prüfe Excel Cities ===")

    cursor.execute("SELECT name, zip_code FROM city")
    pg_cities = set([(row[0].lower(), row[1]) for row in cursor.fetchall()])

    excel_file = "Lets Meet DB Dump.xlsx"
    df = pd.read_excel(excel_file)

    excel_cities = set()
    for index, row in df.iterrows():
        address = row.iloc[1] if len(row) > 1 else ''
        street, zip_code, city_name = process_address(address)

        if city_name and zip_code:
            excel_cities.add((city_name.lower(), zip_code))

    # Vergleiche Städte
    if excel_cities.issubset(pg_cities):
        test_results['cities']['passed'] += len(excel_cities)
    else:
        missing_cities = excel_cities - pg_cities
        test_results['cities']['failed'] += len(missing_cities)
        test_results['cities']['passed'] += len(excel_cities) - len(missing_cities)

        for city_name, zip_code in missing_cities:
            test_results['cities']['details'].append(
                f"City not found in PostgreSQL: {city_name}, {zip_code}"
            )

# Führe alle Tests aus
test_mongodb_users()
test_mongodb_likes()
test_mongodb_messages()
test_xml_users()
test_xml_hobbies()
test_xml_user_hobbies()
test_excel_users()
test_excel_hobbies()
test_excel_cities()

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
mongo_client.close()

print("\n[ALLES GETESTET] Vollständiger Field Test abgeschlossen.")