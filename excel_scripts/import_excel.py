'''

Install pandas: py -m pip install pandas

Use py ./excel_scripts/import_excel.py in the LetsMeet folder!!!
For example: /LetsMeet> py ./excel_scripts/import_excel.py

'''

import pandas as pd
import psycopg2
from psycopg2 import sql



def import_excel_to_postgres(excel_file_path, db_config):

    try:
        excel_data = pd.read_excel(excel_file_path, sheet_name=None)
        print(f"Successfully read Excel file: {excel_file_path}")
        print(f"Found sheets: {list(excel_data.keys())}")
    except Exception as e:
        print(f"Error reading Excel file: {e}")
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
    except Exception as e:
        print(f"Error connecting to database: {e}")
        return

    for  table_name, df in excel_data.items():
        df.columns = [clean_column_name(col) for col in df.columns]

        create_table_sql = generate_create_table_sql(table_name, df, conn)

        try:
            cursor.execute(create_table_sql)
            print(f"Created table: {table_name}")
        except Exception as e:
            print(f"Error creating table {table_name}: {e}")
            conn.rollback()
            continue

        try:
            df = df.where(pd.notnull(df), None)

            insert_sql = generate_insert_sql(table_name, df)

            data_tuples = [tuple(x) for x in df.to_numpy()]

            cursor.executemany(insert_sql, data_tuples)
            conn.commit()

            print(f"Inserted {len(data_tuples)} rows into {table_name}")

        except Exception as e:
            print(f"Error inserting data into {table_name}: {e}")
            conn.rollback()

    cursor.close()
    conn.close()
    print("Database connection closed")

def clean_column_name(column_name):
    col_str = str(column_name)

    col_str = col_str.replace(' ', '_').replace('-', '_').replace('.', '_')

    col_str = ''.join(c if c.isalnum() or c == '_' else '' for c in col_str)

    if col_str and col_str[0].isdigit():
        col_str = f"col_{col_str}"

    return col_str.lower()

def generate_create_table_sql(table_name, df, conn):
    columns = []

    for col_name, col_type in df.dtypes.items():
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

    if conn:
        return sql.SQL('CREATE TABLE IF NOT EXISTS {} ({})').format(
            sql.Identifier(table_name),
            sql.SQL(columns_sql)
        ).as_string(conn)
    else:
        return f'CREATE TABLE IF NOT EXISTS "{table_name}" ({columns_sql})'

def generate_insert_sql(table_name, df):
    columns = [clean_column_name(col) for col in df.columns]
    placeholders = ', '.join(['%s'] * len(columns))
    columns_str = ', '.join([f'"{col}"' for col in columns])

    return f'INSERT INTO "{table_name}" ({columns_str}) VALUES ({placeholders})'


if __name__ == "__main__":
    db_config = {
        'host': 'localhost',
        'port': '5433',
        'database': 'lf8_lets_meet_db',
        'user': 'user',
        'password': 'secret'
    }

    excel_file_path = "Lets Meet DB Dump.xlsx"

    import_excel_to_postgres(excel_file_path, db_config)