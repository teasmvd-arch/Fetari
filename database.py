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


def add_favorite(user_id, movie):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()

    cur.execute(
        """
        SELECT * FROM favorites
        WHERE user_id=? AND movie_id=?
        """,
        (
            user_id,
            movie["id"],
        )
    )

    exists = cur.fetchone()

    if exists:
        conn.close()
        return False


    cur.execute(
        """
        INSERT INTO favorites
        (user_id, movie_id, title, poster, media_type)
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            user_id,
            movie["id"],
            movie["title"],
            movie.get("poster"),
            movie.get("media_type"),
        )
    )

    conn.commit()
    conn.close()

    return True


def get_favorites(user_id):

    conn = sqlite3.connect(DB)
    cur = conn.cursor()

    cur.execute(
        """
        SELECT movie_id, title, poster, media_type
        FROM favorites
        WHERE user_id=?
        """,
        (user_id,)
    )

    rows = cur.fetchall()

    conn.close()

    favorites = []

    for row in rows:
        favorites.append({
            "id": row[0],
            "title": row[1],
            "poster": row[2],
            "media_type": row[3],
        })

    return favorites
