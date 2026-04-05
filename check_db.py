import sqlite3

conn = sqlite3.connect('data/auth.db')
c = conn.cursor()
c.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [r[0] for r in c.fetchall()]
print("Tables:", tables)

for t in tables:
    c.execute(f"SELECT sql FROM sqlite_master WHERE type='table' AND name='{t}'")
    row = c.fetchone()
    if row:
        print(f"\n-- {t} --")
        print(row[0])

conn.close()
