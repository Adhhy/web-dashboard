import sqlite3
import os
import sys

# Add the project root to the python path so we can import config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import Config

def migrate():
    db_path = Config.AUTH_DB_PATH
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get all existing students from the users table
    cursor.execute("SELECT id, username FROM users WHERE role = 'student'")
    student_users = cursor.fetchall()
    
    # Get all subjects from the timetable table
    cursor.execute("SELECT DISTINCT subject_code FROM timetable WHERE subject_code IS NOT NULL")
    subjects = [row[0] for row in cursor.fetchall()]
    
    print(f"Migrating {len(student_users)} students...")
    
    for user_id, username in student_users:
        # Default Student ID to username
        student_id = username
        name = username  # Mapping name to username if missing
        batch = "2023"
        dept = "CSE"
        
        # 1. Insert into students table
        try:
            cursor.execute('''
                INSERT OR IGNORE INTO students (user_id, student_id, name, batch, department)
                VALUES (?, ?, ?, ?, ?)
            ''', (user_id, student_id, name, batch, dept))
            print(f"Migrated student: {username}")
        except Exception as e:
            print(f"Error migrating student {username}: {e}")
            
        # 2. Initialize main_attendance for all subjects
        for subject in subjects:
            try:
                cursor.execute('''
                    INSERT OR IGNORE INTO main_attendance (student_id, subject_code, present_count, duty_leave_count, total_count)
                    VALUES (?, ?, ?, ?, ?)
                ''', (student_id, subject, 0, 0, 0))
            except Exception as e:
                print(f"Error initializing attendance for {username} - {subject}: {e}")
                
    conn.commit()
    conn.close()
    print("Migration and Initialization completed successfully.")

if __name__ == '__main__':
    migrate()
