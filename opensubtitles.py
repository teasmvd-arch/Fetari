import io
import requests

from config import OPENSUBTITLES_API_KEY

BASE_URL = "https://api.opensubtitles.com/api/v1"


def search_subtitles(imdb_id):
    headers = {
        "Api-Key": OPENSUBTITLES_API_KEY,
        "User-Agent": "SubtitleDownloaderBot v1.0",
    }

    response = requests.get(
        f"{BASE_URL}/subtitles",
        headers=headers,
        params={
            "imdb_id": imdb_id.replace("tt", "")
        },
        timeout=20,
    )

    if response.status_code != 200:
        return []

    subtitles = []

    for item in response.json().get("data", []):
        attributes = item.get("attributes", {})
        files = attributes.get("files", [])

        if not files:
            continue

        subtitles.append(
            {
                "language": attributes.get("language"),
                "file_id": files[0]["file_id"],
            }
        )

    return subtitles


def download_subtitle(file_id):
    headers = {
        "Api-Key": OPENSUBTITLES_API_KEY,
        "User-Agent": "SubtitleDownloaderBot v1.0",
    }

    response = requests.post(
        f"{BASE_URL}/download",
        headers=headers,
        json={"file_id": file_id},
        timeout=20,
    )

    if response.status_code != 200:
        return None

    link = response.json().get("link")

    if not link:
        return None

    subtitle = requests.get(link, timeout=30)

    if subtitle.status_code != 200:
        return None

    return io.BytesIO(subtitle.content)
