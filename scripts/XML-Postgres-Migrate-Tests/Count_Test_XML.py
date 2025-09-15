import xml.etree.ElementTree as ET
import pg8000

# PostgreSQL Verbindung
conn = pg8000.connect(
    host='localhost',
    database='lf8_lets_meet_db',
    user='user',
    password='secret',
    port=5433
)
cursor = conn.cursor()

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

# Count in PostgreSQL
cursor.execute("SELECT COUNT(*) FROM users")
pg_user_count = cursor.fetchone()[0]

cursor.execute("SELECT COUNT(*) FROM hobby")
pg_hobby_count = cursor.fetchone()[0]

cursor.execute("SELECT COUNT(*) FROM user_hobby")
pg_user_hobby_count = cursor.fetchone()[0]

# Print results
print("COUNT COMPARISON: XML IMPORT")
print(f"Users:        XML={xml_user_count}, PostgreSQL={pg_user_count}, Match={xml_user_count == pg_user_count}")
print(f"Hobbies:      XML={xml_hobby_count}, PostgreSQL={pg_hobby_count}, Match={xml_hobby_count == pg_hobby_count}")
print(f"User-Hobbies: XML={xml_user_hobby_count}, PostgreSQL={pg_user_hobby_count}, Match={xml_user_hobby_count == pg_user_hobby_count}")

# Calculate success rates
user_match = xml_user_count == pg_user_count
hobby_match = xml_hobby_count == pg_hobby_count
user_hobby_match = xml_user_hobby_count == pg_user_hobby_count

total_tests = 3
passed_tests = sum([user_match, hobby_match, user_hobby_match])
success_rate = (passed_tests / total_tests) * 100

print(f"\nOVERALL: {passed_tests}/{total_tests} tests passed ({success_rate:.1f}%)")

if not user_match:
    print("  ❌ User count mismatch!")
if not hobby_match:
    print("  ❌ Hobby count mismatch!")
if not user_hobby_match:
    print("  ❌ User-Hobby relationship count mismatch!")

if user_match and hobby_match and user_hobby_match:
    print("  ✅ All count tests passed!")

cursor.close()
conn.close()