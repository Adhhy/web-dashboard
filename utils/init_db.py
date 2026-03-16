import sqlite3
import os
import sys
from datetime import datetime
from werkzeug.security import generate_password_hash

# Add the project root to the python path so we can import config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import Config

def init_db():
    """Initialize the database with the required schema and a default admin user."""
    db_path = Config.AUTH_DB_PATH
    
    # Ensure data directory exists (double check)
    os.makedirs(Config.DATA_DIR, exist_ok=True)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create users table
    # Supported roles: student, teacher, advisor, admin
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            username TEXT NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create device_requests table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS device_requests (
            id INTEGER PRIMARY KEY,
            device_id TEXT NOT NULL,
            device_name TEXT NOT NULL,
            device_key TEXT NOT NULL,
            ip_address TEXT,
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Create devices table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS devices (
            id INTEGER PRIMARY KEY,
            device_id TEXT NOT NULL UNIQUE,
            device_name TEXT NOT NULL,
            device_key TEXT NOT NULL,
            ip_address TEXT,
            connection_status TEXT DEFAULT 'connected',
            approved_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Check if admin already exists
    cursor.execute('SELECT id FROM users WHERE username = ?', ('admin',))
    if cursor.fetchone() is None:
        print("Creating default admin user...")
        admin_password_hash = generate_password_hash('admin123')
        cursor.execute('''
            INSERT INTO users (username, password_hash, role)
            VALUES (?, ?, ?)
        ''', ('admin', admin_password_hash, 'admin'))
        print("Admin user created successfully.")
    else:
        print("Admin user already exists. Skipping creation.")
    
    conn.commit()
    conn.close()
    print(f"Database initialized at {db_path}")

if __name__ == '__main__':
    init_db()
