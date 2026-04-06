import sqlite3
import os
import sys
from werkzeug.security import generate_password_hash

# Add the project root to the python path so we can import config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import Config

def seed_database():
    """
    Seeding script for initializing the database with production accounts.
    Handled roles: student, advisor, teacher, admin.
    """
    db_path = Config.AUTH_DB_PATH
    if not os.path.exists(db_path):
        print(f"Error: Database not found at {db_path}. Ensure the database is initialized first.")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    print("--- Seeding Database with Production Accounts ---")

    # --- 1. Students ---
    # Fields: Name, Username, Password, Roll/Student_ID, KTU_ID, Dept, Batch
    students_data = [
        ("Adithyan S", "Adithyan S", "adithyan@123", "7", "CMA23CS007", "CSE", "2023"),
        ("Arun PB", "Arun PB", "arunpb@123", "21", "CMA23CS021", "CSE", "2023"),
        ("Sreehari", "Sreehari", "sreehari@123", "54", "CMA23CS056", "CSE", "2023"),
        ("Suryadev", "Suryadev", "suryadev@123", "55", "CMA23CS057", "CSE", "2023"),
        ("Dinil", "Dinil", "dinil@123", "26", "CMA23CS027", "CSE", "2023")
    ]

    for name, user, pw, roll, ktu, dept, batch in students_data:
        try:
            pw_hash = generate_password_hash(pw)
            cursor.execute("INSERT OR IGNORE INTO users (username, password_hash, role) VALUES (?, ?, ?)", (user, pw_hash, 'student'))
            
            # Fetch user_id
            cursor.execute("SELECT id FROM users WHERE username = ?", (user,))
            user_id = cursor.fetchone()[0]
            
            # Insert profile
            cursor.execute('''
                INSERT OR IGNORE INTO students (user_id, student_id, ktu_id, name, department, batch)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (user_id, roll, ktu, name, dept, batch))
            
            # Initialize cumulative attendance for all subjects in timetable
            cursor.execute("SELECT DISTINCT subject_code FROM timetable WHERE subject_code IS NOT NULL")
            subjects = cursor.fetchall()
            for (subject,) in subjects:
                cursor.execute('''
                    INSERT OR IGNORE INTO main_attendance (student_id, subject_code, present_count, duty_leave_count, total_count)
                    VALUES (?, ?, ?, ?, ?)
                ''', (roll, subject, 0, 0, 0))
            print(f"[SUCCESS] Student {name} ({user}) seeded.")
        except Exception as e:
            print(f"[ERROR] Seeding student {name}: {e}")

    # --- 2. Advisor ---
    # Fields: Name, Username, Password, Dept, Batch
    advisor_data = ("Divya V L", "Advisor1", "advisor1@123", "CSE", "2023")
    try:
        name, user, pw, dept, batch = advisor_data
        pw_hash = generate_password_hash(pw)
        cursor.execute("INSERT OR IGNORE INTO users (username, password_hash, role) VALUES (?, ?, ?)", (user, pw_hash, 'advisor'))
        cursor.execute("SELECT id FROM users WHERE username = ?", (user,))
        user_id = cursor.fetchone()[0]
        cursor.execute('''
            INSERT OR IGNORE INTO advisors (user_id, name, department, batch)
            VALUES (?, ?, ?, ?)
        ''', (user_id, name, dept, batch))
        print(f"[SUCCESS] Advisor {name} ({user}) seeded.")
    except Exception as e:
        print(f"[ERROR] Seeding advisor: {e}")

    # --- 3. Admins ---
    admins_data = [
        ("Adithyan", "admin1@123"),
        ("Sreehari", "admin2@123")
    ]
    for user, pw in admins_data:
        try:
            pw_hash = generate_password_hash(pw)
            cursor.execute("INSERT OR IGNORE INTO users (username, password_hash, role) VALUES (?, ?, ?)", (user, pw_hash, 'admin'))
            print(f"[SUCCESS] Admin {user} seeded.")
        except Exception as e:
            print(f"[ERROR] Seeding admin {user}: {e}")

    # --- 4. Teachers ---
    # Fields: Name, Username, Password, Dept, Subjects Handled (short_codes)
    teachers_data = [
        ("Suchitra M S", "Teacher1", "teacher1@123", "CSE", ["CD"]),
        ("Josemary A", "Teacher2", "teacher2@123", "CSE", ["CGIP"]),
        ("Sreeja Nair M. P", "Teacher3", "teacher3@123", "CSE", ["AAD"]),
        ("Preethy Prabhakar", "Teacher4", "teacher4@123", "CSE", ["PE"])
    ]
    for name, user, pw, dept, subjects in teachers_data:
        try:
            pw_hash = generate_password_hash(pw)
            cursor.execute("INSERT OR IGNORE INTO users (username, password_hash, role) VALUES (?, ?, ?)", (user, pw_hash, 'teacher'))
            cursor.execute("SELECT id FROM users WHERE username = ?", (user,))
            user_id = cursor.fetchone()[0]
            cursor.execute('''
                INSERT OR IGNORE INTO teachers (user_id, name, department)
                VALUES (?, ?, ?)
            ''', (user_id, name, dept))
            for subject in subjects:
                cursor.execute("INSERT OR IGNORE INTO teacher_subjects (user_id, subject_code) VALUES (?, ?)", (user_id, subject))
            print(f"[SUCCESS] Teacher {name} ({user}) seeded.")
        except Exception as e:
            print(f"[ERROR] Seeding teacher {name}: {e}")

    conn.commit()
    conn.close()
    print("\n--- Database Seeding Complete ---")

if __name__ == "__main__":
    seed_database()
