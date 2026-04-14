# database.py
import psycopg2
import psycopg2.extras
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

class Database:
    def __init__(self):
        self.conn_params = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'database': os.getenv('DB_NAME', 'calculator'),
            'user': os.getenv('DB_USER', 'postgres'),
            'password': os.getenv('DB_PASSWORD', '')
        }
        self.init_db()
    
    def get_connection(self):
        return psycopg2.connect(**self.conn_params)
    
    def init_db(self):
        conn = self.get_connection()
        c = conn.cursor()
        
        c.execute('''
            CREATE TABLE IF NOT EXISTS calculations (
                id SERIAL PRIMARY KEY,
                expression TEXT NOT NULL,
                result FLOAT NOT NULL,
                operation VARCHAR(50),
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                source VARCHAR(10) DEFAULT 'web',
                user_identifier TEXT,
                username TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def save_calculation(self, expression, result, operation, source='web', 
                         user_identifier=None, username=None):
        conn = self.get_connection()
        c = conn.cursor()
        
        c.execute('''
            INSERT INTO calculations 
            (expression, result, operation, source, user_identifier, username) 
            VALUES (%s, %s, %s, %s, %s, %s)
        ''', (expression, result, operation, source, user_identifier, username))
        
        conn.commit()
        conn.close()
    
    def get_all(self, source=None):
        conn = self.get_connection()
        c = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        
        if source:
            c.execute('''
                SELECT * FROM calculations 
                WHERE source = %s 
                ORDER BY timestamp DESC
            ''', (source,))
        else:
            c.execute('SELECT * FROM calculations ORDER BY timestamp DESC')
        
        rows = c.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    def get_stats(self, source=None):
        conn = self.get_connection()
        c = conn.cursor()
        
        if source:
            c.execute('''
                SELECT COUNT(*), AVG(result), MIN(result), MAX(result) 
                FROM calculations WHERE source = %s
            ''', (source,))
        else:
            c.execute('''
                SELECT COUNT(*), AVG(result), MIN(result), MAX(result) 
                FROM calculations
            ''')
        
        row = c.fetchone()
        conn.close()
        
        return {
            'count': row[0] or 0,
            'avg': float(row[1]) if row[1] else 0,
            'min': float(row[2]) if row[2] else 0,
            'max': float(row[3]) if row[3] else 0
        }
    
    def clear_all(self):
        conn = self.get_connection()
        c = conn.cursor()
        c.execute('DELETE FROM calculations')
        conn.commit()
        conn.close()
    
    def delete_by_id(self, id):
        conn = self.get_connection()
        c = conn.cursor()
        c.execute('DELETE FROM calculations WHERE id = %s', (id,))
        conn.commit()
        conn.close()