import pg8000

def valiTabel():

    conn = pg8000.connect(
        host='localhost',
        database='lf8_lets_meet_db',
        user='user',
        password='secret',
        port=5433
    )
    cursor = conn.cursor()
    print("[OK] Verbindung zu PostgreSQL hergestellt.")


    cursor.execute("""
    CREATE TABLE IF NOT EXISTS city (
        city_id SERIAL PRIMARY KEY,
        name TEXT,
        zip_code TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS hobby (
        hobby_id SERIAL PRIMARY KEY,
        name TEXT UNIQUE
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        user_id SERIAL PRIMARY KEY,
        first_name TEXT,
        last_name TEXT,
        email TEXT UNIQUE,
        phone_number TEXT,
        birth_date DATE,
        gender TEXT,
        interested_in TEXT,
        city_id INT REFERENCES city(city_id),
        created_at TIMESTAMP,
        updated_at TIMESTAMP
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS user_hobby (
        user_id INT REFERENCES users(user_id),
        hobby_id INT REFERENCES hobby(hobby_id),
        PRIMARY KEY (user_id, hobby_id)
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS friendship (
        user_one_id INT REFERENCES users(user_id),
        user_two_id INT REFERENCES users(user_id),
        created_at TIMESTAMP,
        PRIMARY KEY (user_one_id, user_two_id)
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS likes (
        like_id SERIAL PRIMARY KEY,
        liker_id INT REFERENCES users(user_id),
        liked_id INT REFERENCES users(user_id),
        status TEXT,
        created_at TIMESTAMP
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS messages (
        message_id SERIAL PRIMARY KEY,
        sender_id INT REFERENCES users(user_id),
        receiver_id INT REFERENCES users(user_id),
        conversation_id INT,
        message TEXT,
        sent_at TIMESTAMP
    )
    """)
    conn.commit()
    cursor.close()
    conn.close()
    print("[OK] Tabellen erstellt oder existieren bereits.")
    