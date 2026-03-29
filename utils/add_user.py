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
    
    # Advisor-specific details
    advisor_details = None
    if role == 'advisor':
        print("\nAdvisor Profile Details:")
        name = input("Enter Advisor Full Name: ").strip()
        dept = input("Enter Department: ").strip()
        batch = input("Enter Batch (e.g., CS-2024): ").strip()
        
        if not name or not dept or not batch:
            print("Error: Name, Department, and Batch are required for advisors.")
            return
        advisor_details = (name, dept, batch)
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Start transaction
        cursor.execute("BEGIN TRANSACTION")
        
        cursor.execute('''
            INSERT INTO users (username, password_hash, role)
            VALUES (?, ?, ?)
        ''', (username, password_hash, role))
        
        user_id = cursor.lastrowid
        
        if role == 'advisor' and advisor_details:
            cursor.execute('''
                INSERT INTO advisors (user_id, name, department, batch)
                VALUES (?, ?, ?, ?)
            ''', (user_id, *advisor_details))
            
        conn.commit()
        conn.close()
        print(f"User '{username}' with role '{role}' added successfully.")
        if role == 'advisor':
            print(f"Advisor profile created for '{advisor_details[0]}'.")
    except Exception as e:
        if 'conn' in locals():
            conn.rollback()
            conn.close()
        print(f"An error occurred: {e}")

if __name__ == '__main__':
    add_user()
