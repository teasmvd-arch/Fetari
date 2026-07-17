import sqlite3

DB = "favorites.db"


def init_db():
    conn = sqlite3.connect(DB)
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS favorites (
        user_id INTEGER,
        movie_id INTEGER,
        title TEXT,
        poster TEXT,
        media_type TEXT
    )
    """)

    conn.commit()
    conn.close()
