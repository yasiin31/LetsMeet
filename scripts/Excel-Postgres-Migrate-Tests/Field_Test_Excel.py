import pandas as pd
import pg8000
import re
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from transform_excel import extract_hobbies, process_address, normalize_gender, normalize_interests, process_birthdate


print("=== FIELD TEST FÜR TRANSFORM_EXCEL.PY ===\n")

# PostgreSQL Verbindung
conn = pg8000.connect(
    host='localhost',
    database='lf8_lets_meet_db',
    user='user',
    password='secret',
    port=5433
)
cursor = conn.cursor()

# Excel Datei einlesen
excel_file = "Lets Meet DB Dump.xlsx"
df = pd.read_excel(excel_file)


# Test-Ergebnisse
test_results = {
    'users': {'passed': 0, 'failed': 0, 'details': []},
    'hobbies': {'passed': 0, 'failed': 0, 'details': []},
    'cities': {'passed': 0, 'failed': 0, 'details': []}
}

print("=== Prüfe Users ===")

# Hole alle User-Daten aus PostgreSQL
cursor.execute("""
               SELECT email,
                      first_name,
                      last_name,
                      phone_number,
                      birth_date,
                      gender,
                      interested_in,
                      city_id
               FROM users
               """)
pg_users = {row[0]: row[1:] for row in cursor.fetchall()}

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

print("=== Prüfe Hobbies ===")

# Prüfe Hobby-Verknüpfungen (ohne priority Spalte)
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

print("=== Prüfe Cities ===")

# Prüfe Städte
cursor.execute("SELECT name, zip_code FROM city")
pg_cities = set([(row[0].lower(), row[1]) for row in cursor.fetchall()])

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