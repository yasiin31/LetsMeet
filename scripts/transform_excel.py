'''

Install pandas: py -m pip install pandas
Install pg8000: py -m pip install pg8000

Use py ./scripts/transform_excel.py in the LetsMeet folder!!!
For example: /LetsMeet> py ./scripts/transform_excel.py

'''

import pandas as pd
import pg8000
import re
from validationTabel.validation_tabel import valiTabel

valiTabel()

conn = pg8000.connect(
    host='localhost',
    database='lf8_lets_meet_db',
    user='user',
    password='secret',
    port=5433
)
cursor = conn.cursor()
print("[OK] Verbindung zu PostgreSQL hergestellt.")

excel_file = "Lets Meet DB Dump.xlsx"
df = pd.read_excel(excel_file)
print(f"[OK] Excel-Datei eingelesen: {len(df)} Einträge gefunden")

count_users_updated = 0
count_hobbies_added = 0
count_cities_added = 0

def extract_hobbies(hobby_string):
    hobbies = []
    if pd.isna(hobby_string):
        return hobbies

    hobby_list = str(hobby_string).split(';')

    for hobby in hobby_list:
        hobby = hobby.strip()
        if not hobby:
            continue

        priority_match = re.search(r'%(\d+)%', hobby)
        priority = int(priority_match.group(1)) if priority_match else 50

        hobby_name = re.sub(r'%\d+%', '', hobby).strip()

        if hobby_name:
            hobbies.append((hobby_name, priority))

    return hobbies

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

def normalize_gender(gender_string):
    if pd.isna(gender_string):
        return None

    gender = str(gender_string).lower().strip()
    if gender in ['m', 'male', 'mann']:
        return 'm'
    elif gender in ['w', 'f', 'female', 'frau']:
        return 'w'
    elif gender in ['nb', 'nonbinary', 'nicht binär']:
        return 'nonbinary'
    else:
        return None

def normalize_interests(interest_string):
    if pd.isna(interest_string):
        return None

    interests = str(interest_string).lower().strip()
    result = []

    if 'm' in interests or 'male' in interests or 'mann' in interests:
        result.append('m')
    if 'w' in interests or 'f' in interests or 'female' in interests or 'frau' in interests:
        result.append('w')
    if 'nb' in interests or 'nonbinary' in interests or 'nicht binär' in interests:
        result.append('nonbinary')

    return ','.join(result) if result else None

def process_birthdate(date_string):
    if pd.isna(date_string):
        return None

    try:
        if isinstance(date_string, datetime):
            return date_string.date()
        elif isinstance(date_string, str):
            # Versuche verschiedene Formate
            for fmt in ('%d.%m.%Y', '%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y'):
                try:
                    return datetime.strptime(date_string, fmt).date()
                except ValueError:
                    continue
        return None
    except:
        return None

for index, row in df.iterrows():
    name = row.iloc[0] if len(row) > 0 else ''
    name_parts = name.split(', ')
    if len(name_parts) == 2:
        last_name, first_name = name_parts
    else:
        first_name = name
        last_name = ''

    email = row.iloc[4] if len(row) > 4 else None
    if pd.isna(email):
        continue

    address = row.iloc[1] if len(row) > 1 else ''
    street, zip_code, city_name = process_address(address)

    city_id = None
    if city_name and zip_code:
        cursor.execute("SELECT city_id FROM city WHERE name = %s AND zip_code = %s",
                       (city_name, zip_code))
        result = cursor.fetchone()

        if result:
            city_id = result[0]
        else:
            cursor.execute("INSERT INTO city (name, zip_code) VALUES (%s, %s) RETURNING city_id",
                           (city_name, zip_code))
            city_id = cursor.fetchone()[0]
            count_cities_added += 1

    phone = row.iloc[2] if len(row) > 2 else ''
    if pd.isna(phone):
        phone = None
    else:
        phone = re.sub(r'[^0-9+]', '', str(phone))

    gender = normalize_gender(row.iloc[5] if len(row) > 5 else '')

    interested_in = normalize_interests(row.iloc[6] if len(row) > 6 else '')

    birth_date = process_birthdate(row.iloc[7] if len(row) > 7 else '')

    cursor.execute("""
                   UPDATE users
                   SET first_name = %s, last_name = %s, phone_number = %s,
                       birth_date = %s, gender = %s, interested_in = %s, city_id = %s
                   WHERE email = %s
                       RETURNING user_id
                   """, (first_name, last_name, phone, birth_date, gender, interested_in, city_id, email))

    result = cursor.fetchone()
    if result:
        user_id = result[0]
        count_users_updated += 1

        hobby_string = row.iloc[3] if len(row) > 3 else ''
        hobbies = extract_hobbies(hobby_string)

        for hobby_name, priority in hobbies:
            cursor.execute("SELECT hobby_id FROM hobby WHERE name = %s", (hobby_name,))
            result = cursor.fetchone()

            if result:
                hobby_id = result[0]
            else:
                cursor.execute("INSERT INTO hobby (name) VALUES (%s) RETURNING hobby_id", (hobby_name,))
                hobby_id = cursor.fetchone()[0]

            cursor.execute("""
                           INSERT INTO user_hobby (user_id, hobby_id)
                           VALUES (%s, %s)
                               ON CONFLICT (user_id, hobby_id) DO NOTHING
                           """, (user_id, hobby_id))

            count_hobbies_added += 1

conn.commit()

print(f"[OK] {count_users_updated} Benutzer aktualisiert.")
print(f"[OK] {count_cities_added} Städte hinzugefügt.")
print(f"[OK] {count_hobbies_added} Hobby-Verknüpfungen hinzugefügt.")

cursor.close()
conn.close()
print("[DONE] Excel-Daten-Migration abgeschlossen.")