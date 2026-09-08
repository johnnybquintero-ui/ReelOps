from typing import Any


def validate_release_filters(
    year: int | None,
    month: int | None,
) -> None:
    """Validate optional release filter values."""

    if year is not None and not 1000 <= year <= 9999:
        raise ValueError("year must be a four-digit integer")

    if month is not None and not 1 <= month <= 12:
        raise ValueError("month must be between 1 and 12")


def filter_releases(
    releases: list[dict[str, Any]],
    year: int | None = None,
    month: int | None = None,
) -> list[dict[str, Any]]:
    """Return releases matching validated year and month filters."""

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
