import psycopg2
from psycopg2.extras import RealDictCursor
import os
from dotenv import load_dotenv

load_dotenv()

DB_CONFIG = {
    'host':     os.getenv('DB_HOST', 'localhost'),
    'database': os.getenv('DB_NAME', 'calculator'),
    'user':     os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD', 'ABC!1/2/3'),
}

class Database:
    def get_connection(self):
        return psycopg2.connect(**DB_CONFIG)

    def save_calculation(self, expression, result, operation):
        conn = self.get_connection()
        cur = conn.cursor()
        try:
            cur.execute("""
                INSERT INTO calculations (expression, result, operation)
                VALUES (%s, %s, %s)
            """, (expression, result, operation))
            conn.commit()
        finally:
            cur.close()
            conn.close()

    def get_all(self):
        conn = self.get_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        try:
            cur.execute("SELECT * FROM calculations ORDER BY created_at DESC")
            return cur.fetchall()
        finally:
            cur.close()
            conn.close()

    def clear_all(self):
        conn = self.get_connection()
        cur = conn.cursor()
        try:
            cur.execute("DELETE FROM calculations")
            conn.commit()
        finally:
            cur.close()
            conn.close()

    def get_by_operation(self, operation):
        conn = self.get_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        try:
            cur.execute("""
                SELECT * FROM calculations
                WHERE operation = %s
                ORDER BY created_at DESC
            """, (operation,))
            return cur.fetchall()
        finally:
            cur.close()
            conn.close()

    def search(self, keyword):
        conn = self.get_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        try:
            cur.execute("""
                SELECT * FROM calculations
                WHERE expression ILIKE %s OR result ILIKE %s
                ORDER BY created_at DESC
            """, (f"%{keyword}%", f"%{keyword}%"))
            return cur.fetchall()
        finally:
            cur.close()
            conn.close()

    def get_stats(self):
        conn = self.get_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        try:
            cur.execute("""
                SELECT operation, COUNT(*) as count
                FROM calculations
                GROUP BY operation
                ORDER BY count DESC
            """)
            return cur.fetchall()
        finally:
            cur.close()
            conn.close()

    def delete_by_id(self, record_id):
        conn = self.get_connection()
        cur = conn.cursor()
        try:
            cur.execute("""
                DELETE FROM calculations
                WHERE id = %s
            """, (record_id,))
            conn.commit()
        finally:
            cur.close()
            conn.close()