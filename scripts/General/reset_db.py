'''
Skript zum Löschen aller Tabellen und Zurücksetzen der Datenbank
Verwendung: py ./scripts/General/reset_db.py im LetsMeet-Ordner
'''

import pg8000

def reset_database():
    conn = pg8000.connect(
        host='localhost',
        database='lf8_lets_meet_db',
        user='user',
        password='secret',
        port=5433
    )
    cursor = conn.cursor()
    print("[OK] Verbindung zu PostgreSQL hergestellt.")

    # Deaktiviere Foreign Key Constraints temporär für sauberes Löschen
    cursor.execute("SET session_replication_role = 'replica';")

    # Löschreihenfolge: Child-Tabellen zuerst, dann Parent-Tabellen
    tables_to_drop = [
        'user_hobby',
        'likes',
        'messages',
        'friendship',
        'users',
        'hobby',
        'city'
    ]

    dropped_tables = 0

    for table in tables_to_drop:
        try:
            cursor.execute(f"DROP TABLE IF EXISTS {table} CASCADE")
            print(f"[OK] Tabelle '{table}' gelöscht (falls vorhanden)")
            dropped_tables += 1
        except Exception as e:
            print(f"[ERROR] Fehler beim Löschen von Tabelle '{table}': {e}")

    # Reaktiviere Foreign Key Constraints
    cursor.execute("SET session_replication_role = 'origin';")

    # Setze Sequences zurück (falls auto-increment verwendet wird)
    sequences_to_reset = [
        'city_city_id_seq',
        'hobby_hobby_id_seq',
        'users_user_id_seq',
        'likes_like_id_seq',
        'messages_message_id_seq'
    ]

    reset_sequences = 0

    for sequence in sequences_to_reset:
        try:
            cursor.execute(f"DROP SEQUENCE IF EXISTS {sequence} CASCADE")
            print(f"[OK] Sequence '{sequence}' zurückgesetzt")
            reset_sequences += 1
        except Exception as e:
            print(f"[INFO] Sequence '{sequence}' konnte nicht zurückgesetzt werden: {e}")

    conn.commit()
    cursor.close()
    conn.close()

    print(f"\n[ZUSAMMENFASSUNG]")
    print(f"Gelöschte Tabellen: {dropped_tables}")
    print(f"Zurückgesetzte Sequences: {reset_sequences}")
    print("[DONE] Datenbank erfolgreich zurückgesetzt!")

if __name__ == "__main__":
    print("START: Datenbank zurücksetzen")
    print("WARNUNG: Dieser Vorgang löscht ALLE Daten!")
    confirmation = input("Sind Sie sicher? (ja/NEIN): ")

    if confirmation.lower() == 'ja':
        reset_database()
    else:
        print("Abbruch: Datenbank wurde nicht zurückgesetzt.")