from typing import Any

import requests


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
