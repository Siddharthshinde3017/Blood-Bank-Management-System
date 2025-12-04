# import sqlite3
# from werkzeug.security import generate_password_hash
# import os

# DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "blood_bank.db")

# conn = sqlite3.connect(DB_PATH)
# cur = conn.cursor()

# ---------- DONORS TABLE ----------
# cur.execute("""
# CREATE TABLE IF NOT EXISTS donors (
#     id INTEGER PRIMARY KEY AUTOINCREMENT,
#     name TEXT NOT NULL,
#     blood_group TEXT NOT NULL,
#     mobile TEXT,
#     email TEXT UNIQUE NOT NULL,
#     password TEXT NOT NULL,
#     last_donation TEXT
# )
# """)

# # ---------- DONATION HISTORY TABLE ----------
# cur.execute("""
# CREATE TABLE IF NOT EXISTS donation_history (
#     id INTEGER PRIMARY KEY AUTOINCREMENT,
#     donor_id INTEGER NOT NULL,
#     donation_date TEXT NOT NULL,
#     units INTEGER NOT NULL,
#     location TEXT,
#     blood_group TEXT,
#     FOREIGN KEY(donor_id) REFERENCES donors(id)
# )
# """)

# # ---------- BLOOD REQUESTS TABLE ----------
# cur.execute("""
# CREATE TABLE IF NOT EXISTS blood_requests (
#     id INTEGER PRIMARY KEY AUTOINCREMENT,
#     donor_id INTEGER NOT NULL,
#     blood_group TEXT NOT NULL,
#     units INTEGER NOT NULL,
#     request_date TEXT NOT NULL,
#     FOREIGN KEY(donor_id) REFERENCES donors(id)
# )
# """)

# # ---------- ADMIN TABLE ----------
# cur.execute("""
# CREATE TABLE IF NOT EXISTS admin (
#     id INTEGER PRIMARY KEY AUTOINCREMENT,
#     username TEXT UNIQUE NOT NULL,
#     password TEXT NOT NULL
# )
# """)

# # ---------- ADD DEFAULT ADMIN ----------
# admin = cur.execute("SELECT * FROM admin WHERE username = 'admin'").fetchone()
# if not admin:
#     cur.execute(
#         "INSERT INTO admin(username, password) VALUES(?, ?)",
#         ("admin", generate_password_hash("admin123"))
#     )
#     print(" Default admin created: username='admin', password='admin123'")
# else:
#     print(" Admin already exists")

# conn.commit()
# conn.close()
# print(" Database created successfully at:", DB_PATH)

import sqlite3
import os

db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "blood_bank.db")
conn = sqlite3.connect(db_path)
cur = conn.cursor()

# Add 'status' column with default value 'Pending'
try:
    cur.execute("ALTER TABLE blood_requests ADD COLUMN status TEXT DEFAULT 'Pending'")
    print("✅ 'status' column added to blood_requests table")
except sqlite3.OperationalError:
    print("ℹ️ 'status' column already exists")

conn.commit()
conn.close()
