import sqlite3
import os
import sys

# Add the project root to the python path so we can import config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import Config

def init_schema():
    db_path = Config.AUTH_DB_PATH
    print(f"Initializing database at {db_path}...")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 1. Create Timetable Table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS timetable (
        day TEXT,
        period INTEGER,
        subject_code TEXT,
        PRIMARY KEY (day, period)
    )
    ''')
    
    # 2. Create Students Table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS students (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER UNIQUE NOT NULL,
        student_id TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL,
        batch TEXT,
        department TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )
    ''')
    
    # 3. Create Main Attendance Table (Cumulative)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS main_attendance (
        student_id TEXT,
        subject_code TEXT,
        present_count INTEGER DEFAULT 0,
        duty_leave_count INTEGER DEFAULT 0,
        total_count INTEGER DEFAULT 0,
        PRIMARY KEY (student_id, subject_code)
    )
    ''')
    
    # 4. Create Session Calculation Status Table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS session_calculation_status (
        date TEXT,
        session_type TEXT,
        is_calculated INTEGER DEFAULT 0,
        PRIMARY KEY (date, session_type)
    )
    ''')
    
    # 5. Create History Attendance Table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS history_attendance (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT,
        student_id TEXT,
        period TEXT,
        status_code TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # 6. Populate Timetable from hardcoded SQL-like data
    timetable_data = [
        ('MONDAY', 1, 'AAD'), ('MONDAY', 2, 'IEFT'), ('MONDAY', 3, 'PE'), ('MONDAY', 4, 'CGIP'),
        ('MONDAY', 5, 'CD'), ('MONDAY', 6, 'AAD'), ('MONDAY', 7, 'CD'),
        
        ('TUESDAY', 1, 'CD'), ('TUESDAY', 2, 'CGIP'), ('TUESDAY', 3, 'PE'), ('TUESDAY', 4, 'CD'),
        ('TUESDAY', 5, None), ('TUESDAY', 6, None), ('TUESDAY', 7, None),
        
        ('WEDNESDAY', 1, 'PE'), ('WEDNESDAY', 2, 'AAD'), ('WEDNESDAY', 3, 'IEFT'), ('WEDNESDAY', 4, None),
        ('WEDNESDAY', 5, None), ('WEDNESDAY', 6, None), ('WEDNESDAY', 7, None),
        
        ('THURSDAY', 1, 'AAD'), ('THURSDAY', 2, 'IEFT'), ('THURSDAY', 3, 'PE'), ('THURSDAY', 4, 'CD'),
        ('THURSDAY', 5, 'CCW'), ('THURSDAY', 6, 'AAD'), ('THURSDAY', 7, 'CGIP'),
        
        ('FRIDAY', 1, 'CGIP'), ('FRIDAY', 2, None), ('FRIDAY', 3, None), ('FRIDAY', 4, None),
        ('FRIDAY', 5, None), ('FRIDAY', 6, 'CGIP'), ('FRIDAY', 7, 'PE'),
    ]
    
    for row in timetable_data:
        cursor.execute("INSERT OR REPLACE INTO timetable VALUES (?, ?, ?)", row)
    
    conn.commit()
    conn.close()
    print("Attendance schema initialized successfully.")

if __name__ == '__main__':
    init_schema()
