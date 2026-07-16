import requests
from config import SUBDL_API_KEY


def search_subdl(imdb_id):
    url = "https://api.subdl.com/api/v1/subtitles"

    params = {
        "api_key": SUBDL_API_KEY,
        "imdb_id": imdb_id
    }

    try:
        response = requests.get(url, params=params, timeout=10)

        if response.status_code != 200:
            return []

        data = response.json()

        results = []

        for sub in data.get("subtitles", []):
            results.append({
                "language": sub.get("lang"),
                "release": sub.get("release_name"),
                "url": sub.get("url"),
                "source": "SubDL"
            })

        return results

    except Exception:
        return []
