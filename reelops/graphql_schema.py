from typing import Any

import strawberry
from strawberry.types import Info

from reelops.query import (
    filter_releases,
    validate_release_filters,
)


@strawberry.type
class Release:
    tmdb_id: int
    title: str
    release_date: str
    original_language: str
    overview: str
    popularity: float | None
    genres: list[str]


def build_release(record: dict[str, Any]) -> Release:
    """Convert an internal release record to a GraphQL type."""

    return Release(
        tmdb_id=record["tmdb_id"],
        title=record["title"],
        release_date=record["release_date"],
        original_language=record["original_language"],
        overview=record["overview"],
        popularity=record["popularity"],
        genres=record["genres"],
    )


@strawberry.type
class Query:
    @strawberry.field
    def releases(
        self,
        info: Info,
        year: int | None = None,
        month: int | None = None,
    ) -> list[Release]:
        """Resolve cached releases with optional filters."""

        validate_release_filters(year, month)

        cache = info.context["cache"]
        records = filter_releases(
            cache["releases"],
            year=year,
            month=month,
        )

        return [build_release(record) for record in records]


schema = strawberry.Schema(query=Query)
