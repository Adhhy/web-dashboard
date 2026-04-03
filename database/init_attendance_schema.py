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
    
    # 0. Create Subjects Table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS subjects (
        code TEXT PRIMARY KEY,
        full_name TEXT NOT NULL,
        credits INTEGER,
        semester INTEGER,
        subject_type TEXT,
        short_code TEXT UNIQUE
    )
    ''')
    
    # Preload Exact Subjects mapping per KTU
    subjects_data = [
        ('CST302', 'Compiler Design', 4, 6, 'Core', 'CD'),
        ('CST304', 'Computer Graphics and Image Processing', 4, 6, 'Core', 'CGIP'),
        ('CST306', 'Algorithm Analysis and Design', 4, 6, 'Core', 'AAD'),
        ('CST362', 'Programming in Python', 3, 6, 'Elective', 'PE'),
        ('HUT300', 'Industrial Economics and Foreign Trade', 3, 6, 'Humanities', 'IEFT'),
        ('CST308', 'Comprehensive Course Work', 1, 6, 'Lab', 'CCW'),
        ('CSL332', 'Networking Lab', 2, 6, 'Lab', None),
        ('CSD334', 'Mini Project', 2, 6, 'Project', None)
    ]
    cursor.executemany("INSERT OR IGNORE INTO subjects VALUES (?, ?, ?, ?, ?, ?)", subjects_data)

    # 1. Create Timetable Table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS timetable (
        day TEXT,
        period INTEGER,
        subject_code TEXT,
        PRIMARY KEY (day, period),
        FOREIGN KEY (subject_code) REFERENCES subjects(short_code)
    )
    ''')
    
    # 2. Create Students Table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS students (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER UNIQUE NOT NULL,
        student_id TEXT UNIQUE NOT NULL,
        ktu_id TEXT,
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
        PRIMARY KEY (student_id, subject_code),
        FOREIGN KEY (subject_code) REFERENCES subjects(short_code)
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
    
    # 6. Create Policy Logs Table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS policy_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT, 
        session_id INTEGER, 
        device_id TEXT, 
        student_id TEXT, 
        student_name TEXT, 
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP, 
        date TEXT, 
        event_type TEXT, 
        period TEXT, 
        session_type TEXT, 
        recognition_status TEXT, 
        late_entry BOOLEAN DEFAULT 0, 
        bus_delay BOOLEAN DEFAULT 0, 
        status TEXT, 
        system_message TEXT, 
        advisor_id INTEGER, 
        action_timestamp DATETIME, 
        FOREIGN KEY(session_id) REFERENCES sessions(id), 
        FOREIGN KEY(advisor_id) REFERENCES users(id)
    )
    ''')
    
    # 7. Create Morning Attendance Table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS morning_attendance (
        student_id TEXT, 
        date TEXT, 
        P1 TEXT DEFAULT 'A', 
        P2 TEXT DEFAULT 'A', 
        P3 TEXT DEFAULT 'A', 
        P4 TEXT DEFAULT 'A', 
        PRIMARY KEY(student_id, date)
    )
    ''')
    
    # 8. Create Afternoon Attendance Table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS afternoon_attendance (
        student_id TEXT, 
        date TEXT, 
        P5 TEXT DEFAULT 'A', 
        P6 TEXT DEFAULT 'A', 
        P7 TEXT DEFAULT 'A', 
        PRIMARY KEY(student_id, date)
    )
    ''')
    
    # 10. Populate Timetable from hardcoded SQL-like data
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
