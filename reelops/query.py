from typing import Any


def filter_releases(
    releases: list[dict[str, Any]],
    year: int | None = None,
    month: int | None = None,
) -> list[dict[str, Any]]:
    """Filter releases by optional release year and month."""

    result = []

    for release in releases:
        release_date = release["release_date"]
        release_year = int(release_date[:4])
        release_month = int(release_date[5:7])

        if year is not None and release_year != year:
            continue

        if month is not None and release_month != month:
            continue

        result.append(release)

    return result
