import re
import requests

from config import TMDB_API_KEY

BASE_URL = "https://api.themoviedb.org/3"


def parse_query(query):
    """
    Supports:
    Breaking Bad
    Breaking Bad S01E01
    Breaking.Bad.S01E01
    Breaking Bad 1x01
    """

    season = None
    episode = None

    match = re.search(
        r"(.*?)[ ._-]*(?:S(\d+)E(\d+)|(\d+)x(\d+))",
        query,
        re.IGNORECASE,
    )

    if match:
        title = match.group(1)

        if match.group(2):
            season = int(match.group(2))
            episode = int(match.group(3))
        else:
            season = int(match.group(4))
            episode = int(match.group(5))

        title = (
            title.replace(".", " ")
            .replace("_", " ")
            .strip()
        )

        return title, season, episode

    return (
        query.replace(".", " ").replace("_", " ").strip(),
        None,
        None,
    )


def search_movie(query):
    title, season, episode = parse_query(query)

    headers = {
        "Authorization": f"Bearer {TMDB_API_KEY}",
        "accept": "application/json",
    }

    response = requests.get(
        f"{BASE_URL}/search/multi",
        headers=headers,
        params={
            "query": title,
            "include_adult": "false",
            "language": "en-US",
            "page": 1,
        },
        timeout=20,
    )

    print("Search title:", title)
    print("Status:", response.status_code)

    if response.status_code != 200:
        print(response.text)
        return []

    results = response.json().get("results", [])

    final_results = []

    for item in results:

        if item.get("media_type") not in ["movie", "tv"]:
            continue

        item["season"] = season
        item["episode"] = episode
       
        item["poster"] = (
          "https://image.tmdb.org/t/p/w500"
          + item["poster_path"]
          if item.get("poster_path")
          else None
       )
       
        final_results.append(item)

    return final_results
def get_imdb_id(media_type, tmdb_id):
    headers = {
        "Authorization": f"Bearer {TMDB_API_KEY}",
        "accept": "application/json",
    }

    if media_type == "movie":
        url = f"{BASE_URL}/movie/{tmdb_id}"
    else:
        url = f"{BASE_URL}/tv/{tmdb_id}/external_ids"

    response = requests.get(
        url,
        headers=headers,
        timeout=20,
    )

    if response.status_code != 200:
        return None

    data = response.json()

    if media_type == "tv":
        imdb_id = data.get("imdb_id")
    else:
        imdb_id = data.get("imdb_id")

    return {
        "imdb_id": imdb_id,
        "title": data.get("title") or data.get("name"),
    }
   
if __name__ == "__main__":
    print(search_movie("Avatar"))
