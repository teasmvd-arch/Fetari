import requests

from config import TMDB_API_KEY

BASE_URL = "https://api.themoviedb.org/3"


def search_movie(query):
    headers = {
        "Authorization": f"Bearer {TMDB_API_KEY}",
        "accept": "application/json",
    }

    response = requests.get(
        f"{BASE_URL}/search/multi",
        headers=headers,
        params={
            "query": query,
            "include_adult": "false",
            "language": "en-US",
            "page": 1,
        },
        timeout=20,
    )

    if response.status_code != 200:
        return None

    results = response.json().get("results", [])

    for item in results:
        if item.get("media_type") in ("movie", "tv"):
            return item

    return None


def get_imdb_id(media_type, tmdb_id):
    headers = {
        "Authorization": f"Bearer {TMDB_API_KEY}",
        "accept": "application/json",
    }

    if media_type == "movie":
        url = f"{BASE_URL}/movie/{tmdb_id}/external_ids"
    else:
        url = f"{BASE_URL}/tv/{tmdb_id}/external_ids"

    response = requests.get(
        url,
        headers=headers,
        timeout=20,
    )

    if response.status_code != 200:
        return None

    return response.json().get("imdb_id")
