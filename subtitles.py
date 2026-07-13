import requests
import re

from config import TMDB_API_KEY

BASE_URL = "https://api.themoviedb.org/3"


def clean_query(query):
    # . ወደ space ቀይር
    query = query.replace(".", " ")

    # S01E01, S1E1, S01 E01 አስወግድ
    query = re.sub(
        r"\bS\d{1,2}\s*E\d{1,2}\b",
        "",
        query,
        flags=re.IGNORECASE,
    )

    # Season 1 Episode 1 አስወግድ
    query = re.sub(
        r"\bSeason\s*\d+\s*Episode\s*\d+\b",
        "",
        query,
        flags=re.IGNORECASE,
    )

    # Video quality አስወግድ
    query = re.sub(
        r"\b(2160p|1080p|720p|480p)\b",
        "",
        query,
        flags=re.IGNORECASE,
    )

    # Release tags አስወግድ
    query = re.sub(
        r"\b(WEB[- ]?DL|WEBRip|BluRay|BRRip|HDRip|DVDRip|HDTV|NF|AMZN)\b",
        "",
        query,
        flags=re.IGNORECASE,
    )

    # Codec አስወግድ
    query = re.sub(
        r"\b(x264|x265|H264|H265|HEVC|AAC|DDP5\.1|DD5\.1)\b",
        "",
        query,
        flags=re.IGNORECASE,
    )

    # ብዙ space አንድ አድርግ
    query = " ".join(query.split())

    return query


def search_movie(query):
    query = clean_query(query)

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
            return {
                "id": item.get("id"),
                "media_type": item.get("media_type"),
                "title": item.get("title") or item.get("name"),
                "release_date": item.get("release_date"),
                "first_air_date": item.get("first_air_date"),
                "vote_average": item.get("vote_average"),
                "poster_path": item.get("poster_path"),
            }

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
