'''

Use py ./excel_scripts/import_excel.py in the LetsMeet folder!!!
For example: \LetsMeet> py ./excel_scripts/import_excel.py

'''

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

    # Process each sheet in the Excel file
    for sheet_name, df in excel_data.items():
        # Clean column names (remove spaces, special characters, etc.)
        df.columns = [clean_column_name(col) for col in df.columns]

        # Convert pandas data types to PostgreSQL compatible types
        table_name = f"import_{clean_table_name(sheet_name)}"

        # Create table if it doesn't exist
        create_table_sql = generate_create_table_sql(table_name, df, conn)

        try:
            cursor.execute(create_table_sql)
            print(f"Created table: {table_name}")
        except Exception as e:
            print(f"Error creating table {table_name}: {e}")
            conn.rollback()
            continue

        # Insert data into the table
        try:
            # Convert NaN values to None for PostgreSQL
            df = df.where(pd.notnull(df), None)

            # Generate INSERT statements
            insert_sql = generate_insert_sql(table_name, df)

            # Convert DataFrame to list of tuples for executemany
            data_tuples = [tuple(x) for x in df.to_numpy()]

            # Execute INSERT statements
            cursor.executemany(insert_sql, data_tuples)
            conn.commit()

            print(f"Inserted {len(data_tuples)} rows into {table_name}")

        except Exception as e:
            print(f"Error inserting data into {table_name}: {e}")
            conn.rollback()

    # Close database connection
    cursor.close()
    conn.close()
    print("Database connection closed")

def clean_column_name(column_name):
    # Clean column names for PostgreSQL compatibility
    # Convert to string if not already
    col_str = str(column_name)

    # Replace spaces and special characters with underscores
    col_str = col_str.replace(' ', '_').replace('-', '_').replace('.', '_')

    # Remove any other non-alphanumeric characters except underscores
    col_str = ''.join(c if c.isalnum() or c == '_' else '' for c in col_str)

    # Ensure it doesn't start with a number
    if col_str and col_str[0].isdigit():
        col_str = f"col_{col_str}"

    # Convert to lowercase
    return col_str.lower()

def clean_table_name(table_name):
    # Clean table names for PostgreSQL compatibility
    # Apply similar cleaning as column names
    return clean_column_name(table_name)

def generate_create_table_sql(table_name, df, conn):
    # Generate CREATE TABLE SQL statement based on DataFrame structure
    columns = []

    for col_name, col_type in df.dtypes.items():
        # Map pandas dtypes to PostgreSQL types
        if col_type == 'int64':
            pg_type = 'BIGINT'
        elif col_type == 'float64':
            pg_type = 'DOUBLE PRECISION'
        elif col_type == 'bool':
            pg_type = 'BOOLEAN'
        elif col_type == 'datetime64[ns]':
            pg_type = 'TIMESTAMP'
        else:
            pg_type = 'TEXT'

        clean_col = clean_column_name(col_name)
        columns.append(f'"{clean_col}" {pg_type}')

    columns_sql = ', '.join(columns)

    # Use SQL composition if connection is available
    if conn:
        return sql.SQL('CREATE TABLE IF NOT EXISTS {} ({})').format(
            sql.Identifier(table_name),
            sql.SQL(columns_sql)
        ).as_string(conn)
    else:
        return f'CREATE TABLE IF NOT EXISTS "{table_name}" ({columns_sql})'

def generate_insert_sql(table_name, df):
    # Generate INSERT SQL statement for a table
    columns = [clean_column_name(col) for col in df.columns]
    placeholders = ', '.join(['%s'] * len(columns))
    columns_str = ', '.join([f'"{col}"' for col in columns])

    return f'INSERT INTO "{table_name}" ({columns_str}) VALUES ({placeholders})'


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