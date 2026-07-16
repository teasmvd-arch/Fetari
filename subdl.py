import io
import os
import zipfile
import requests

from config import SUBDL_API_KEY


BASE_URL = "https://api.subdl.com/api/v1"
DOWNLOAD_URL = "https://dl.subdl.com"


def search_subdl(
    imdb_id,
    season=None,
    episode=None,
):
    params = {
        "api_key": SUBDL_API_KEY,
        "imdb_id": imdb_id,
        "unpack": 1,
        "subs_per_page": 30,
    }

    if season is not None:
        params["season_number"] = season

    if episode is not None:
        params["episode_number"] = episode
        params["type"] = "tv"
    else:
        params["type"] = "movie"

    try:
        r = requests.get(
            f"{BASE_URL}/subtitles",
            params=params,
            timeout=20,
        )

        if r.status_code != 200:
            return []

        data = r.json()

        if not data.get("status"):
            return []

        subtitles = []

        for sub in data.get("subtitles", []):

            # unpacked files (best)
            if sub.get("unpack_files"):

                for f in sub["unpack_files"]:

                    subtitles.append({
                        "attributes": {
                            "language": f["language"].lower(),
                            "release": f["release_name"],
                            "files": [{
                                "file_id": None,
                                "file_name": f["name"],
                                "download_url": DOWNLOAD_URL + f["url"],
                                "source": "subdl",
                           }],
                        }
                    })

            else:

                      subtitles.append({
                          "attributes": {
                              "language": "unknown",
                              "release": sub.get("release_name", "Subtitle"),
                              "files": [{
                                  "file_id": None,
                                  "file_name": sub.get("name", "subtitle.zip"),
                                  "download_url": DOWNLOAD_URL + sub["url"],
                                  "source": "subdl",
                              }],
                          }
                       })

        return subtitles

    except Exception as e:
        print("SubDL Error:", e)
        return []


def download_subdl(download_url):
    try:

        r = requests.get(
            download_url,
            params={
                "api_key": SUBDL_API_KEY,
            },
            timeout=60,
        )

        if r.status_code != 200:
            return None

        # zip file
        if download_url.endswith(".zip"):

            z = zipfile.ZipFile(
                io.BytesIO(r.content)
            )

            for name in z.namelist():

                if name.endswith(
                    (
                        ".srt",
                        ".ass",
                        ".ssa",
                        ".sub",
                    )
                ):

                    return {
                        "filename": os.path.basename(name),
                        "content": io.BytesIO(
                            z.read(name)
                        ),
                    }

        # single subtitle
        return {
            "filename": "subtitle.srt",
            "content": io.BytesIO(r.content),
        }

    except Exception as e:
        print("SubDL Download Error:", e)
        return None
