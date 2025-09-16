import pandas as pd
import pg8000
import re
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from transform_excel import process_address


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

# Count aus PostgreSQL-Datenbank
cursor.execute("SELECT COUNT(*) FROM users")
pg_user_count = cursor.fetchone()[0]

cursor.execute("SELECT COUNT(*) FROM user_hobby")
pg_hobby_count = cursor.fetchone()[0]

cursor.execute("SELECT COUNT(*) FROM city")
pg_city_count = cursor.fetchone()[0]

# Print results
print("COUNT COMPARISON EXCEL TRANSFORMATION:")
print(f"Users:     Excel={excel_user_count}, PostgreSQL={pg_user_count}, Match={excel_user_count == pg_user_count}")
print(f"Hobbies:   Excel={excel_hobby_entries}, PostgreSQL={pg_hobby_count}, Match={excel_hobby_entries == pg_hobby_count}")
print(f"Cities:    Excel={excel_city_entries}, PostgreSQL={pg_city_count}, Match={excel_city_entries == pg_city_count}")

# Calculate success rates
user_match = excel_user_count == pg_user_count
hobby_match = excel_hobby_entries == pg_hobby_count
city_match = excel_city_entries == pg_city_count

total_tests = 3
passed_tests = sum([user_match, hobby_match, city_match])
success_rate = (passed_tests / total_tests) * 100

print(f"\nOVERALL: {passed_tests}/{total_tests} tests passed ({success_rate:.1f}%)")

if not user_match:
    print("  ❌ User count mismatch!")
if not hobby_match:
    print("  ❌ Hobby count mismatch!")
if not city_match:
    print("  ❌ City count mismatch!")

if user_match and hobby_match and city_match:
    print("  ✅ All count tests passed!")

cursor.close()
conn.close()
print("[DONE] Excel Count Test abgeschlossen.")