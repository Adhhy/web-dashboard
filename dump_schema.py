import sqlite3

try:
    conn = sqlite3.connect('data/auth.db')
    cursor = conn.cursor()
    tables = ['policy_logs', 'morning_attendance', 'afternoon_attendance']
    with open('schemas.txt', 'w') as f:
        for t in tables:
            res = cursor.execute(f"SELECT sql FROM sqlite_master WHERE name='{t}'").fetchone()
            if res:
                f.write(res[0] + '\n')
            else:
                f.write(f"No schema found for {t}\n")
    conn.close()
    print("Schemas dumped to schemas.txt")
except Exception as e:
    print(f"Error: {e}")
