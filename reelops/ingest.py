import json
from pathlib import Path
from typing import Any

import requests


def fetch_tmdb_upcoming_releases(
    tmdb_url: str,
    tmdb_read_token: str,
    region: str = "GB",
    page: int = 1,
) -> dict[str, Any]:
    """Fetch one page of upcoming movie releases from TMDb."""

    response = requests.get(
        tmdb_url,
        headers={
            "Authorization": f"Bearer {tmdb_read_token}",
            "Accept": "application/json",
        },
        params={
            "region": region,
            "page": page,
        },
        timeout=10,
    )

    response.raise_for_status()
    return response.json()


def save_raw_payload_to_bronze(
    raw_payload: dict[str, Any],
    bronze_path: Path,
) -> Path:
    """Save the raw source payload to the Bronze layer."""

    bronze_path.parent.mkdir(
        # creates parent folders where necessary
        parents=True,
        # prevents error if the folder already exists
        exist_ok=True,
    )

    with bronze_path.open(
        mode="w",
        encoding="utf-8",
    ) as bronze_file:
        json.dump(
            raw_payload,
            bronze_file,
            indent=4,
            ensure_ascii=False,
        )

    return bronze_path


def fetch_tmdb_genres(
    tmdb_base_url: str,
    tmdb_read_token: str,
) -> dict[str, Any]:
    """Fetch the list of available movie genres from TMDb."""

    response = requests.get(
        f"{tmdb_base_url.rstrip('/')}/genre/movie/list",
        headers={
            "Authorization": f"Bearer {tmdb_read_token}",
            "Accept": "application/json",
        },
        params={
            "language": "en",
        },
        timeout=10,
    )

    response.raise_for_status()
    return response.json()
