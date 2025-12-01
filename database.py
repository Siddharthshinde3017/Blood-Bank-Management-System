import sqlite3

def create_db():
    conn = sqlite3.connect("blood_bank.db")
    cur = conn.cursor()


    # Donor Table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS donors(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        blood_group TEXT,
        mobile TEXT,
        email TEXT UNIQUE,
        password TEXT
    )
    """)

    # Admin Table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS admin(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT
    )
    """)

    # Insert default admin (username=admin , password=admin123)
    cur.execute("SELECT * FROM admin")
    if not cur.fetchone():
        cur.execute("INSERT INTO admin(username, password) VALUES(?, ?)",
                    ("admin", "admin123"))
    
    conn.commit()
    conn.close()




# Run DB creation
if __name__ == "__main__":
    create_db()
