import logging
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from reelops.ingest import (
    fetch_tmdb_genres,
    fetch_tmdb_upcoming_releases,
    save_raw_payload_to_bronze,
)
from reelops.storage import save_cache_response
from reelops.transform import (
    build_cache_response,
    build_genre_map,
    transform_releases,
)

logger = logging.getLogger(__name__)


def refresh_release_cache(
    tmdb_base_url: str,
    tmdb_read_token: str,
    region: str = "GB",
    page: int = 1,
    data_root: Path = Path("data"),
) -> dict[str, int]:
    """Fetch releases, preserve raw data and update the API cache."""

    tmdb_base_url = tmdb_base_url.rstrip("/")

    raw_payload = fetch_tmdb_upcoming_releases(
        f"{tmdb_base_url}/movie/upcoming",
        tmdb_read_token,
        region,
        page,
    )

    genre_payload = fetch_tmdb_genres(
        tmdb_base_url,
        tmdb_read_token,
    )

    snapshot_path = (
        data_root
        / "raw"
        / "tmdb"
        / "upcoming"
        / f"extract_date={datetime.now(tz=UTC).date().isoformat()}"
        / f"run_id={uuid4()}"
        / f"page_{page}.json"
    )

    save_raw_payload_to_bronze(
        raw_payload,
        snapshot_path,
    )

    genre_map = build_genre_map(genre_payload)

    releases, stats = transform_releases(
        raw_payload,
        genre_map,
    )

    cache_response = build_cache_response(
        releases,
        region,
    )

    cache_path = data_root / "api-cache" / "latest_upcoming_releases.json"

    save_cache_response(
        cache_response,
        cache_path,
    )

    logger.info(
        "Release processing statistics: %s",
        stats,
    )

    return stats
