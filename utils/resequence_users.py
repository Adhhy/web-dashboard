import sqlite3
import os
import sys

# Add the project root to the python path so we can import config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import Config

def resequence_users():
    """Re-assign contiguous IDs to users in the database."""
    db_path = Config.AUTH_DB_PATH
    
    if not os.path.exists(db_path):
        print(f"Error: Database not found at {db_path}.")
        return

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 1. Fetch all users ordered by ID
        cursor.execute('SELECT username, password_hash, role, created_at FROM users ORDER BY id')
        users = cursor.fetchall()
        
        if not users:
            print("No users found to re-sequence.")
            conn.close()
            return
            
        print(f"Found {len(users)} users. Re-sequencing...")
        
        # 2. Clear the table
        cursor.execute('DELETE FROM users')
        # Reset the internal SQLite sequence if it exists (though we removed AUTOINCREMENT)
        cursor.execute("DELETE FROM sqlite_sequence WHERE name='users'")
        
        # 3. Re-insert with fresh IDs
        cursor.executemany('''
            INSERT INTO users (username, password_hash, role, created_at)
            VALUES (?, ?, ?, ?)
        ''', users)
        
        conn.commit()
        conn.close()
        print("Users re-sequenced successfully. IDs are now contiguous (1, 2, 3...).")
        
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == '__main__':
    resequence_users()
