import psycopg2
from psycopg2 import sql

conn = None
cur = None

try:
    conn = psycopg2.connect(
        dbname="postgres",
        user="postgres",
        password="ABC!1/2/3",
        host="localhost",
        port=5432
    )

    conn.autocommit = True
    cur = conn.cursor()

    db_name = "calculator"
    cur.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(db_name)))
    print(f"Database '{db_name}' created successfully.")

except psycopg2.errors.DuplicateDatabase:
    print(f"Database '{db_name}' already exists.")
except psycopg2.Error as e:
    print(f"Database error: {e}")
finally:
    if cur:
        cur.close()
    if conn:
        conn.close()