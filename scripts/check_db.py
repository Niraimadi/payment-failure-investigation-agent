import sqlite3
from pathlib import Path

db_path = Path("data/payments.db")

conn = sqlite3.connect(db_path)

tables = conn.execute(
    "SELECT name FROM sqlite_master WHERE type='table'"
).fetchall()

print("Tables found:", tables)

if tables:
    rows = conn.execute("SELECT * FROM transactions").fetchall()
    print("\nTransaction records:")
    for row in rows:
        print(row)
else:
    print("No tables found in the database.")

conn.close()