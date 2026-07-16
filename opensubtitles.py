import io
import requests

from config import OPENSUBTITLES_API_KEY

BASE_URL = "https://api.opensubtitles.com/api/v1"

HEADERS = {
    "Api-Key": OPENSUBTITLES_API_KEY,
    "User-Agent": "SubtitleDownloaderBot v2.0",
}
def search_subtitles(imdb_id, season=None, episode=None):
    params = {
        "imdb_id": imdb_id.replace("tt", "")
    }

    if season is not None:
        params["season_number"] = season

    if episode is not None:
        params["episode_number"] = episode

    response = requests.get(
        f"{BASE_URL}/subtitles",
        headers=HEADERS,
        params=params,
        timeout=20,
    )

    if response.status_code != 200:
        return []

    return response.json().get("data", [])

def get_languages(subtitles):
    languages = []

    for sub in subtitles:
        lang = sub["attributes"].get("language")

        if lang and lang not in languages:
            languages.append(lang)

    return sorted(languages)
def get_releases(subtitles, language):
    releases = []

    for sub in subtitles:

        attributes = sub.get(
            "attributes",
            {}
        )

        if attributes.get("language") != language:
            continue


        release = attributes.get(
            "release",
            "Unknown Release"
        )


        files = attributes.get(
            "files",
            []
        )

        if not files:
            continue


        file = files[0]


        item = {
            "release": release,
            "filename": file.get(
                "file_name",
                "subtitle.srt"
            ),
            "source": file.get(
                "source",
                "opensubtitles"
            ),
        }


        # OpenSubtitles
        if item["source"] == "opensubtitles":

            item["file_id"] = file.get(
                "file_id"
            )


        # SubDL
        elif item["source"] == "subdl":

            item["download_url"] = file.get(
                "download_url"
            )


        releases.append(item)


    return releases[:10]

def download_subtitle(file_id):
    response = requests.post(
        f"{BASE_URL}/download",
        headers=HEADERS,
        json={"file_id": file_id},
        timeout=20,
    )

    if response.status_code != 200:
        return None

    data = response.json()

    download_url = data.get("link")
    filename = data.get("file_name", "subtitle.srt")

    if not download_url:
        return None

    subtitle = requests.get(download_url, timeout=30)

    if subtitle.status_code != 200:
        return None

    return {
        "filename": filename,
        "content": io.BytesIO(subtitle.content),
    }
