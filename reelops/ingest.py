from pathlib import Path
from typing import Any

import requests
import json

import os
from dotenv import load_dotenv

load_dotenv()

def fetch_tmdb_upcoming_releases(
    tmdb_url: str,
    tmdb_read_token: str,
) -> dict[str, Any]:
    """Fetch one page of upcoming movie releases from TMDb."""

    response = requests.get(
        tmdb_url,
        headers={
            "Authorization": f"Bearer {tmdb_read_token}",
            "Accept": "application/json",
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
        #creates parent folders where necessary
        parents=True,
        #prevents error if the folder already exists
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