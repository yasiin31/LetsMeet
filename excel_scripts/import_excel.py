import pandas as pd
import psycopg2
from psycopg2 import sql


def import_excel_to_postgres(excel_file_path, db_config):

    # Import data from Excel file to PostgreSQL database
    # Read Excel file
    try:
        # Read all sheets from the Excel file
        excel_data = pd.read_excel(excel_file_path, sheet_name=None)
        print(f"Successfully read Excel file: {excel_file_path}")
        print(f"Found sheets: {list(excel_data.keys())}")
    except Exception as e:
        print(f"Error reading Excel file: {e}")
        return

    # Connect to PostgreSQL database
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
    except Exception as e:
        print(f"Error connecting to database: {e}")
        return


    cursor.close()
    conn.close()
    print("Database connection closed")


if __name__ == "__main__":
    # Database configuration
    db_config = {
        'host': 'localhost',
        'port': '5432',
        'database': 'lf8_lets_meet_db',
        'user': 'user',
        'password': 'secret'
    }

    # Excel file path
    excel_file_path = "Lets Meet DB Dump.xlsx"

    # Run the import
    import_excel_to_postgres(excel_file_path, db_config)