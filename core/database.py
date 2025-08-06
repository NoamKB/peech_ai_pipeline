import sqlite3
from datetime import datetime

conn = None
cursor = None

def init_db(db_path="news.db"):
    global conn, cursor
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS headlines (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source TEXT,
            headline TEXT,
            category TEXT,
            raw_label TEXT,
            confidence REAL,
            scraped_at TIMESTAMP
        )
    """)
    conn.commit()

def save_to_db(source, headline, category, raw_label, confidence):
    cursor.execute(
        "INSERT INTO headlines (source, headline, category, raw_label, confidence, scraped_at) VALUES (?, ?, ?, ?, ?, ?)",
        (source, headline, category, raw_label, confidence, datetime.now())
    )
    conn.commit()

def close_db():
    conn.close()
