import logging
from datetime import date, datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)


def validate_release(release: dict[str, Any]) -> list[str]:
    """Return validation errors for one raw TMDb release."""

    errors = []

    required_fields = (
        "id",
        "title",
        "release_date",
        "original_language",
    )

    for field in required_fields:
        if field not in release:
            errors.append(f"Missing required field: {field}")

    release_id = release.get("id")

    if (
        isinstance(release_id, bool)
        or not isinstance(release_id, int)
        or release_id <= 0
    ):
        errors.append("'id' must be a positive integer")

    title = release.get("title")

    if not isinstance(title, str) or not title.strip():
        errors.append("'title' must be a non-empty string")

    original_language = release.get("original_language")

    if not isinstance(original_language, str) or not original_language.strip():
        errors.append("'original_language' must be a non-empty string")

    release_date = release.get("release_date")

    if not isinstance(release_date, str) or not release_date:
        errors.append("'release_date' must be a non-empty string")
    else:
        try:
            parsed_date = date.fromisoformat(release_date)

            if parsed_date.isoformat() != release_date:
                errors.append("'release_date' must use YYYY-MM-DD format")
        except ValueError:
            errors.append("'release_date' must be a valid date in YYYY-MM-DD format")

    genre_ids = release.get("genre_ids", [])

    if not isinstance(genre_ids, list) or not all(
        isinstance(genre_id, int) and not isinstance(genre_id, bool)
        for genre_id in genre_ids
    ):
        errors.append("'genre_ids' must be a list of integers")

    return errors


def build_genre_map(
    genre_payload: dict[str, Any],
) -> dict[int, str]:
    """Transform a raw TMDb genre response into an ID-to-name lookup."""

    return {genre["id"]: genre["name"] for genre in genre_payload["genres"]}


def normalise_release(
    release: dict[str, Any],
    genre_map: dict[int, str],
) -> dict[str, Any]:
    """Return a normalised version of one validated TMDb release."""

    popularity = release.get("popularity")

    if isinstance(popularity, bool) or not isinstance(popularity, (int, float)):
        popularity = None

    overview = release.get("overview")

    if isinstance(overview, str):
        overview = overview.strip()
    else:
        overview = ""

    genre_names = []

    for genre_id in release.get("genre_ids", []):
        genre_name = genre_map.get(genre_id)

        if genre_name is None:
            logger.warning("Unknown genre ID: %s", genre_id)
            continue

        genre_names.append(genre_name)

    return {
        "tmdb_id": release["id"],
        "title": release["title"].strip(),
        "release_date": release["release_date"],
        "original_language": release["original_language"].strip(),
        "overview": overview,
        "popularity": popularity,
        "genres": genre_names,
    }


def transform_releases(
    raw_payload: dict[str, Any],
    genre_map: dict[int, str],
) -> tuple[list[dict[str, Any]], dict[str, int]]:
    """Validate, normalise and deduplicate a TMDb release payload."""

    raw_releases = raw_payload.get("results", [])

    normalised_releases = []
    seen_tmdb_ids = set()

    stats = {
        "retrieved": len(raw_releases),
        "accepted": 0,
        "rejected": 0,
        "deduplicated": 0,
    }

    for raw_release in raw_releases:
        errors = validate_release(raw_release)

        if errors:
            stats["rejected"] += 1
            logger.warning(
                "Rejected release %s: %s",
                raw_release.get("id"),
                errors,
            )
            continue

        normalised_release = normalise_release(
            raw_release,
            genre_map,
        )

        tmdb_id = normalised_release["tmdb_id"]

        if tmdb_id in seen_tmdb_ids:
            stats["deduplicated"] += 1
            continue

        seen_tmdb_ids.add(tmdb_id)
        normalised_releases.append(normalised_release)
        stats["accepted"] += 1

    return normalised_releases, stats


def build_cache_response(
    releases: list[dict[str, Any]],
    region: str,
) -> dict[str, Any]:
    """Build a cache response payload for the TMDb releases."""

    return {
        "region": region,
        "release_count": len(releases),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "releases": releases,
    }
