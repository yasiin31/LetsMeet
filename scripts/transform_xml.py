'''

Use py ./scripts/transform_xml.py in the LetsMeet folder!!!
For example: /LetsMeet> py ./scripts/transform_xml.py

'''

import xml.etree.ElementTree as ET
import psycopg2
from psycopg2 import sql

def create_tables_if_not_exist(cursor):
    cursor.execute("""
                   CREATE TABLE IF NOT EXISTS xml_users (
                                                               email VARCHAR(255) PRIMARY KEY,
                       name VARCHAR(255)
                       )
                   """)

    cursor.execute("""
                   CREATE TABLE IF NOT EXISTS user_hobbies (
                                                                      id SERIAL PRIMARY KEY,
                                                                      email VARCHAR(255) REFERENCES xml_users(email),
                       hobby VARCHAR(255),
                       UNIQUE(email, hobby)
                       )
                   """)

    print("Tables created or already exist")

def parse_xml_and_import(xml_file_path, db_config):
    try:
        tree = ET.parse(xml_file_path)
        root = tree.getroot()
        print(f"Successfully parsed XML file: {xml_file_path}")
    except Exception as e:
        print(f"Error parsing XML file: {e}")
        return

    try:
        conn = psycopg2.connect(
            host=db_config['host'],
            port=db_config['port'],
            database=db_config['database'],
            user=db_config['user'],
            password=db_config['password']
        )
        cursor = conn.cursor()
        print("Successfully connected to PostgreSQL database")

        create_tables_if_not_exist(cursor)
        conn.commit()

    except Exception as e:
        print(f"Error connecting to database: {e}")
        return

    users_count = 0
    hobbies_count = 0

    for user_elem in root.findall('user'):
        try:
            email = user_elem.find('email').text.strip() if user_elem.find('email') is not None else None
            name = user_elem.find('name').text.strip() if user_elem.find('name') is not None else None

            if not email or not name:
                print(f"Skipping user with missing data: {email}, {name}")
                continue

            cursor.execute("""
                           INSERT INTO xml_users (email, name)
                           VALUES (%s, %s)
                               ON CONFLICT (email) DO NOTHING
                           """, (email, name))

            users_count += 1

            hobbies_elem = user_elem.find('hobbies')
            if hobbies_elem is not None:
                for hobby_elem in hobbies_elem.findall('hobby'):
                    hobby = hobby_elem.text.strip() if hobby_elem.text else None

                    if hobby:
                        cursor.execute("""
                                       INSERT INTO user_hobbies (email, hobby)
                                       VALUES (%s, %s)
                                           ON CONFLICT DO NOTHING
                                       """, (email, hobby))
                        hobbies_count += 1

        except Exception as e:
            print(f"Error processing user {email}: {e}")
            conn.rollback()
            continue

    conn.commit()
    print(f"Successfully imported {users_count} users and {hobbies_count} hobbies")

    cursor.close()
    conn.close()
    print("Database connection closed")

if __name__ == "__main__":
    db_config = {
        'host': 'localhost',
        'port': '5433',
        'database': 'lf8_lets_meet_db',
        'user': 'user',
        'password': 'secret'
    }

    xml_file_path = "Lets_Meet_Hobbies.xml"

    parse_xml_and_import(xml_file_path, db_config)