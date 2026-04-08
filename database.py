# database.py (MODIFIED)
import sqlite3
from datetime import datetime

class Database:
    def __init__(self, db_path='calculator.db'):
        self.db_path = db_path
        self.init_db()
    
    def init_db(self):
        """Initialize database with source column"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        # Check if source column exists, if not add it
        c.execute("PRAGMA table_info(calculations)")
        columns = [col[1] for col in c.fetchall()]
        
        if 'source' not in columns:
            try:
                c.execute("ALTER TABLE calculations ADD COLUMN source TEXT DEFAULT 'web'")
                c.execute("ALTER TABLE calculations ADD COLUMN user_identifier TEXT")
                c.execute("ALTER TABLE calculations ADD COLUMN username TEXT")
            except sqlite3.OperationalError:
                pass
        
        # Create table if it doesn't exist
        c.execute('''CREATE TABLE IF NOT EXISTS calculations
                    (id INTEGER PRIMARY KEY AUTOINCREMENT,
                     expression TEXT NOT NULL,
                     result REAL NOT NULL,
                     operation TEXT,
                     timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                     source TEXT DEFAULT 'web',
                     user_identifier TEXT,
                     username TEXT)''')
        
        conn.commit()
        conn.close()
    
    def save_calculation(self, expression, result, operation, source='web', 
                         user_identifier=None, username=None):
        """Save calculation with source tracking"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('''INSERT INTO calculations 
                    (expression, result, operation, source, user_identifier, username) 
                    VALUES (?, ?, ?, ?, ?, ?)''',
                 (expression, result, operation, source, user_identifier, username))
        conn.commit()
        conn.close()
    
    def get_all(self, source=None):
        """Get all calculations, optionally filtered by source"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        
        if source:
            c.execute('''SELECT * FROM calculations 
                        WHERE source = ? 
                        ORDER BY timestamp DESC''', (source,))
        else:
            c.execute('SELECT * FROM calculations ORDER BY timestamp DESC')
        
        rows = c.fetchall()
        conn.close()
        return [dict(row) for row in rows]
    
    def get_stats(self, source=None):
        """Get statistics with source filter"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        query = 'SELECT COUNT(*), AVG(result), MIN(result), MAX(result) FROM calculations'
        params = []
        
        if source:
            query += ' WHERE source = ?'
            params = [source]
        
        c.execute(query, params)
        count, avg, min_val, max_val = c.fetchone()
        conn.close()
        
        return {
            'count': count or 0,
            'avg': avg or 0,
            'min': min_val or 0,
            'max': max_val or 0
        }
    
    # Keep your existing methods (clear_all, delete_by_id, etc.)