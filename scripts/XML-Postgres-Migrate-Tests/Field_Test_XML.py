import xml.etree.ElementTree as ET
import pg8000

print("=== FIELD TEST FÜR TRANSFORM_XML.PY ===\n")

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

# XML-Datei einlesen
xml_file_path = "Lets_Meet_Hobbies.xml"
tree = ET.parse(xml_file_path)
root = tree.getroot()
user_count = len(root.findall('user'))
print(f"[OK] XML-Datei erfolgreich gelesen - {user_count} User gefunden")

# Test-Ergebnisse
test_results = {
    'users': {'passed': 0, 'failed': 0, 'details': []},
    'hobbies': {'passed': 0, 'failed': 0, 'details': []},
    'user_hobbies': {'passed': 0, 'failed': 0, 'details': []}
}

# Test 1: Users-Datenintegrität
print("=== Prüfe Users ===")
cursor.execute("SELECT email, first_name, last_name, phone_number, birth_date, gender, interested_in FROM users")
pg_users = {row[0]: row[1:] for row in cursor.fetchall()}

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

# Test 2: Hobbies-Datenintegrität
print("=== Prüfe Hobbies ===")
cursor.execute("SELECT name FROM hobby")
pg_hobbies = {row[0] for row in cursor.fetchall()}

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

# Test 3: User-Hobby-Verknüpfungen
print("=== Prüfe User-Hobby-Verknüpfungen ===")
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

# Ergebnisse ausgeben
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

print("\n[ALLES GETESTET] Vollabgleich abgeschlossen.")