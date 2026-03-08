import sqlite3
import os
import sys
import getpass
from werkzeug.security import generate_password_hash

# Add the project root to the python path so we can import config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import Config

def add_user():
    """Manually add a new user to the authentication database."""
    db_path = Config.AUTH_DB_PATH
    
    if not os.path.exists(db_path):
        print(f"Error: Database not found at {db_path}. Run init_db.py first.")
        return

    username = input("Enter username: ").strip()
    if not username:
        print("Username cannot be empty.")
        return
        
    password = getpass.getpass("Enter password: ")
    if not password:
        print("Password cannot be empty.")
        return
        
    roles_allowed = ['student', 'teacher', 'advisor', 'admin']
    print(f"Available roles: {', '.join(roles_allowed)}")
    role = input("Enter role: ").strip().lower()
    
    if role not in roles_allowed:
        print(f"Error: Invalid role. Must be one of {roles_allowed}")
        return
    
    password_hash = generate_password_hash(password)
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO users (username, password_hash, role)
            VALUES (?, ?, ?)
        ''', (username, password_hash, role))
        
        conn.commit()
        conn.close()
        print(f"User '{username}' with role '{role}' added successfully.")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == '__main__':
    add_user()
