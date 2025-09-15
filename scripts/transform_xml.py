'''

Install pg8000: py -m pip install pg8000

Use py ./scripts/transform_xml.py in the LetsMeet folder!!!
For example: /LetsMeet> py ./scripts/transform_xml.py

'''

import xml.etree.ElementTree as ET
import pg8000
from validationTabel.validation_tabel import valiTabel

valiTabel()
xml_file_path = "Lets_Meet_Hobbies.xml"
conn = pg8000.connect(
    host='localhost',
    database='lf8_lets_meet_db',
    user='user',
    password='secret',
    port=5433
)
cursor = conn.cursor()
print("[OK] Verbindung zu PostgreSQL hergestellt.")

tree = ET.parse(xml_file_path)
root = tree.getroot()

count_hobbies_added = 0
count_user_hobbies_added = 0
users_not_found = 0

for user_elem in root.findall('user'):
    email_elem = user_elem.find('email')
    if email_elem is None or email_elem.text is None:
        continue
    email = email_elem.text.strip().lower()

    hobbies = []

    for hobby_elem in user_elem.findall('hobby'):
        if hobby_elem.text is not None:
            hobbies.append(hobby_elem.text.strip())

    hobbies_elem = user_elem.find('hobbies')
    if hobbies_elem is not None:
        for hobby_elem in hobbies_elem.findall('hobby'):
            if hobby_elem.text is not None:
                hobbies.append(hobby_elem.text.strip())

    if not hobbies:
        continue

    try:
        cursor.execute("SELECT user_id FROM users WHERE LOWER(email) = %s", (email,))
        user_result = cursor.fetchone()
    except Exception as e:
        print(f"[ERROR] Datenbankfehler bei User-Lookup für {email}: {e}")
        continue

    if not user_result:
        print(f"[WARN] User mit E-Mail {email} nicht gefunden. Überspringe Hobbys.")
        users_not_found += 1
        continue

    user_id = user_result[0]

    for hobby_name in hobbies:
        if not hobby_name:
            continue

        try:
            cursor.execute("SELECT hobby_id FROM hobby WHERE name = %s", (hobby_name,))
            hobby_result = cursor.fetchone()
        except Exception as e:
            print(f"[ERROR] Datenbankfehler bei Hobby-Lookup für '{hobby_name}': {e}")
            continue

        if hobby_result:
            hobby_id = hobby_result[0]
        else:
            try:
                cursor.execute(
                    "INSERT INTO hobby (name) VALUES (%s) RETURNING hobby_id",
                    (hobby_name,)
                )
                hobby_id = cursor.fetchone()[0]
                count_hobbies_added += 1
                print(f"[OK] Neues Hobby '{hobby_name}' hinzugefügt (ID: {hobby_id})")
            except Exception as e:
                print(f"[ERROR] Fehler beim Erstellen des Hobbys '{hobby_name}': {e}")
                continue

        try:
            cursor.execute(
                "SELECT 1 FROM user_hobby WHERE user_id = %s AND hobby_id = %s",
                (user_id, hobby_id)
            )
            if cursor.fetchone():
                continue
        except Exception as e:
            print(f"[ERROR] Datenbankfehler bei User-Hobby-Check: {e}")
            continue

        try:
            cursor.execute(
                "INSERT INTO user_hobby (user_id, hobby_id) VALUES (%s, %s)",
                (user_id, hobby_id)
            )
            count_user_hobbies_added += 1
        except Exception as e:
            print(f"[ERROR] Fehler beim Erstellen der User-Hobby-Verbindung: {e}")
            continue

conn.commit()

print(f"\n[ZUSAMMENFASSUNG]")
print(f"Neue Hobbys hinzugefügt: {count_hobbies_added}")
print(f"User-Hobby-Verbindungen erstellt: {count_user_hobbies_added}")
print(f"User nicht gefunden: {users_not_found}")

cursor.close()
conn.close()
print("[DONE] XML-Import abgeschlossen.")
