import os


BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
TMDB_API_KEY = os.getenv("TMDB_API_KEY", "").strip()
OPENSUBTITLES_API_KEY = os.getenv("OPENSUBTITLES_API_KEY", "").strip()
SUBDL_API_KEY = os.getenv("SUBDL_API_KEY")

def check_config():
    missing = []

    if not BOT_TOKEN:
        missing.append("BOT_TOKEN")

    if not TMDB_API_KEY:
        missing.append("TMDB_API_KEY")

    if not OPENSUBTITLES_API_KEY:
        missing.append("OPENSUBTITLES_API_KEY")

    if missing:
        raise RuntimeError(
            "Missing environment variables: "
            + ", ".join(missing)
        )
