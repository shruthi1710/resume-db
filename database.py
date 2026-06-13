import sqlite3

def get_db():
    conn = sqlite3.connect("Resumes.DB")
    conn.row_factory = sqlite3.Row
    return conn 

def init_db():
    conn = get_db()
    conn.execute("""
    Create table if not exists resumes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    title TEXT NOT NULL,
    location TEXT NOT NULL,
    exp INTEGER NOT NULL, 
    email TEXT,
    phone TEXT,
    company TEXT, 
    edu TEXT, 
    skills TEXT, 
    summary TEXT,
    status TEXT DEFAULT 'active'
    )
   """)
    conn.commit()
    conn.close()