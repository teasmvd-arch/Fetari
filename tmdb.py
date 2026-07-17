import re


def parse_query(query):

    season = None
    episode = None

    match = re.search(
        r"[sS](\d+)\s*[eE](\d+)",
        query
    )

    if match:
        season = int(match.group(1))
        episode = int(match.group(2))

        query = re.sub(
            r"[sS]\d+\s*[eE]\d+",
            "",
            query
        )


    match = re.search(
        r"(\d+)x(\d+)",
        query
    )

    if match:
        season = int(match.group(1))
        episode = int(match.group(2))

        query = re.sub(
            r"\d+x\d+",
            "",
            query
        )


    return query.strip(), season, episode
