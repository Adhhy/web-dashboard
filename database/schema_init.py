import sqlite3
import os
from datetime import datetime
from werkzeug.security import generate_password_hash
from config import Config

def get_db_connection():
    return sqlite3.connect(Config.AUTH_DB_PATH)

def init_all_tables():
    """
    Consolidated initialization for all 18+ database tables.
    Ensures the entire system schema is present and seeded on startup.
    """
    db_path = Config.AUTH_DB_PATH
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    print(f"Verifying database schema at {db_path}...")

    # 1. Users Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # 2. Students Table
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

    # 3. Advisors Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS advisors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE NOT NULL,
            name TEXT NOT NULL,
            department TEXT NOT NULL,
            batch TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')

    # 4. Teachers Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS teachers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE NOT NULL,
            name TEXT NOT NULL,
            department TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')

    # 5. Teacher Subjects Map
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS teacher_subjects (
            user_id INTEGER NOT NULL,
            subject_code TEXT NOT NULL,
            PRIMARY KEY (user_id, subject_code),
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')

    # 6. Subjects Table
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

    # 7. Timetable Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS timetable (
            day TEXT,
            period INTEGER,
            subject_code TEXT,
            PRIMARY KEY (day, period),
            FOREIGN KEY (subject_code) REFERENCES subjects(short_code)
        )
    ''')

    # 8. Main Attendance (Cumulative)
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

    # 9. Session Calculation Status
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS session_calculation_status (
            date TEXT,
            session_type TEXT,
            is_calculated INTEGER DEFAULT 0,
            PRIMARY KEY (date, session_type)
        )
    ''')

    # 10. History Attendance
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

    # 11. Policy Logs (Raw facial recognition logs)
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

    # 12. Morning Attendance (Daily View)
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

    # 13. Afternoon Attendance (Daily View)
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

    # 14. Device Requests (Onboarding)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS device_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            device_id TEXT NOT NULL,
            device_name TEXT NOT NULL,
            device_key TEXT NOT NULL,
            ip_address TEXT,
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # 15. Devices (Approved)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS devices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            device_id TEXT NOT NULL UNIQUE,
            device_name TEXT NOT NULL,
            device_key TEXT NOT NULL,
            ip_address TEXT,
            connection_status TEXT DEFAULT 'connected',
            approved_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # 16. Sessions (Hardware Session State)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            status TEXT DEFAULT 'idle',
            started_at TIMESTAMP,
            stopped_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # 17. Device Commands (Remote Polling)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS device_commands (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            device_id TEXT NOT NULL UNIQUE,
            command TEXT DEFAULT 'idle',
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # 18. Duty Leave Requests
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS duty_leave_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id TEXT NOT NULL,
            subject_code TEXT NOT NULL,
            date TEXT NOT NULL,
            periods TEXT NOT NULL,
            reason TEXT NOT NULL,
            description TEXT,
            evidence_path TEXT,
            advisor_status TEXT DEFAULT 'Pending',
            faculty_status TEXT DEFAULT 'Pending',
            admin_status TEXT DEFAULT 'Pending',
            current_state TEXT DEFAULT 'PendingAdvisor',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # --- Seeding Data ---

    # A. Subjects
    subjects_seed = [
        ('CST302', 'Compiler Design', 4, 6, 'Core', 'CD'),
        ('CST304', 'Computer Graphics and Image Processing', 4, 6, 'Core', 'CGIP'),
        ('CST306', 'Algorithm Analysis and Design', 4, 6, 'Core', 'AAD'),
        ('CST362', 'Programming in Python', 3, 6, 'Elective', 'PE'),
        ('HUT300', 'Industrial Economics and Foreign Trade', 3, 6, 'Humanities', 'IEFT'),
        ('CST308', 'Comprehensive Course Work', 1, 6, 'Lab', 'CCW'),
        ('CSL332', 'Networking Lab', 2, 6, 'Lab', 'NL'),
        ('CSD334', 'Mini Project', 2, 6, 'Project', 'MP')
    ]
    cursor.executemany("INSERT OR IGNORE INTO subjects VALUES (?, ?, ?, ?, ?, ?)", subjects_seed)

    # B. Timetable
    timetable_seed = [
        ('MONDAY', 1, 'AAD'), ('MONDAY', 2, 'IEFT'), ('MONDAY', 3, 'PE'), ('MONDAY', 4, 'CGIP'),
        ('MONDAY', 5, 'CD'), ('MONDAY', 6, 'AAD'), ('MONDAY', 7, 'CD'),
        ('TUESDAY', 1, 'CD'), ('TUESDAY', 2, 'CGIP'), ('TUESDAY', 3, 'PE'), ('TUESDAY', 4, 'CD'),
        ('WEDNESDAY', 1, 'PE'), ('WEDNESDAY', 2, 'AAD'), ('WEDNESDAY', 3, 'IEFT'),
        ('THURSDAY', 1, 'AAD'), ('THURSDAY', 2, 'IEFT'), ('THURSDAY', 3, 'PE'), ('THURSDAY', 4, 'CD'),
        ('THURSDAY', 5, 'CCW'), ('THURSDAY', 6, 'AAD'), ('THURSDAY', 7, 'CGIP'),
        ('FRIDAY', 1, 'CGIP'), ('FRIDAY', 6, 'CGIP'), ('FRIDAY', 7, 'PE')
    ]
    for row in timetable_seed:
        cursor.execute("INSERT OR REPLACE INTO timetable (day, period, subject_code) VALUES (?, ?, ?)", row)

    # C. Admin User
    cursor.execute('SELECT id FROM users WHERE username = ?', ('admin',))
    if cursor.fetchone() is None:
        pw_hash = generate_password_hash('admin123')
        cursor.execute("INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)", 
                      ('admin', pw_hash, 'admin'))

    # D. Hardware Session & Command Resets
    cursor.execute('SELECT id FROM sessions LIMIT 1')
    if cursor.fetchone() is None:
        cursor.execute("INSERT INTO sessions (status) VALUES ('idle')")
    else:
        cursor.execute("UPDATE sessions SET status = 'idle' WHERE status != 'idle'")
    
    cursor.execute("UPDATE device_commands SET command = 'idle'")

    conn.commit()
    conn.close()
    print("Database verification complete. All tables initialized.")

if __name__ == '__main__':
    init_all_tables()
