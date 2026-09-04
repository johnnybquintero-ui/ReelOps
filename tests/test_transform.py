import json
import logging
from datetime import datetime
from pathlib import Path

import pytest

from reelops.transform import (
    build_cache_response,
    build_genre_map,
    normalise_release,
    transform_releases,
    validate_release,
)


@pytest.fixture
def valid_release():
    return {
        "id": 1101412,
        "title": "Fall 2: Deadpoint",
        "release_date": "2026-09-09",
        "original_language": "en",
        "overview": "A film synopsis.",
        "popularity": 51.7971,
        "genre_ids": [53, 28],
    }


@pytest.fixture
def genre_map():
    return {
        28: "Action",
        53: "Thriller",
    }


def test_validate_release_returns_no_errors_for_valid_release(
    valid_release,
):
    errors = validate_release(valid_release)

    assert errors == []


@pytest.mark.parametrize(
    "missing_field",
    [
        "id",
        "title",
        "release_date",
        "original_language",
    ],
)
def test_validate_release_reports_missing_required_field(
    valid_release,
    missing_field,
):
    valid_release.pop(missing_field)

    errors = validate_release(valid_release)

    assert f"Missing required field: {missing_field}" in errors


@pytest.mark.parametrize(
    "invalid_id",
    [
        0,
        -1,
        "123",
        True,
        None,
    ],
)
def test_validate_release_rejects_invalid_id(
    valid_release,
    invalid_id,
):
    valid_release["id"] = invalid_id

    errors = validate_release(valid_release)

    assert "'id' must be a positive integer" in errors


@pytest.mark.parametrize(
    "invalid_title",
    [
        "",
        "   ",
        None,
        123,
    ],
)
def test_validate_release_rejects_invalid_title(
    valid_release,
    invalid_title,
):
    valid_release["title"] = invalid_title

    errors = validate_release(valid_release)

    assert "'title' must be a non-empty string" in errors


def test_validate_release_rejects_invalid_original_language(
    valid_release,
):
    valid_release["original_language"] = ""

    errors = validate_release(valid_release)

    assert "'original_language' must be a non-empty string" in errors


@pytest.mark.parametrize(
    "invalid_date",
    [
        "banana",
        "2026-02-30",
        "09/09/2026",
    ],
)
def test_validate_release_rejects_invalid_date(
    valid_release,
    invalid_date,
):
    valid_release["release_date"] = invalid_date

    errors = validate_release(valid_release)

    assert "'release_date' must be a valid date in YYYY-MM-DD format" in errors


def test_validate_release_rejects_date_without_hyphens(
    valid_release,
):
    valid_release["release_date"] = "20260909"

    errors = validate_release(valid_release)

    assert "'release_date' must use YYYY-MM-DD format" in errors


def test_validate_release_accepts_missing_genre_ids(
    valid_release,
):
    valid_release.pop("genre_ids")

    errors = validate_release(valid_release)

    assert errors == []


def test_validate_release_accepts_empty_genre_list(
    valid_release,
):
    valid_release["genre_ids"] = []

    errors = validate_release(valid_release)

    assert errors == []


@pytest.mark.parametrize(
    "invalid_genre_ids",
    [
        "53",
        [53, "28"],
        [True],
        None,
    ],
)
def test_validate_release_rejects_invalid_genre_ids(
    valid_release,
    invalid_genre_ids,
):
    valid_release["genre_ids"] = invalid_genre_ids

    errors = validate_release(valid_release)

    assert "'genre_ids' must be a list of integers" in errors


def test_build_genre_map_returns_id_to_name_lookup():
    genre_payload = {
        "genres": [
            {"id": 28, "name": "Action"},
            {"id": 53, "name": "Thriller"},
        ]
    }

    result = build_genre_map(genre_payload)

    assert result == {
        28: "Action",
        53: "Thriller",
    }


def test_normalise_release_returns_expected_fields(
    valid_release,
    genre_map,
):
    result = normalise_release(valid_release, genre_map)

    assert result == {
        "tmdb_id": 1101412,
        "title": "Fall 2: Deadpoint",
        "release_date": "2026-09-09",
        "original_language": "en",
        "overview": "A film synopsis.",
        "popularity": 51.7971,
        "genres": ["Thriller", "Action"],
    }


@pytest.mark.parametrize(
    "invalid_popularity",
    [
        None,
        True,
        "51.7971",
        [],
    ],
)
def test_normalise_release_converts_invalid_popularity_to_none(
    valid_release,
    genre_map,
    invalid_popularity,
):
    valid_release["popularity"] = invalid_popularity

    result = normalise_release(valid_release, genre_map)

    assert result["popularity"] is None


def test_normalise_release_handles_missing_optional_fields(
    valid_release,
    genre_map,
):
    valid_release.pop("overview")
    valid_release.pop("popularity")
    valid_release.pop("genre_ids")

    result = normalise_release(valid_release, genre_map)

    assert result["overview"] == ""
    assert result["popularity"] is None
    assert result["genres"] == []


def test_normalise_release_logs_and_skips_unknown_genre(
    valid_release,
    genre_map,
    caplog,
):
    valid_release["genre_ids"] = [53, 999999]

    with caplog.at_level(logging.WARNING):
        result = normalise_release(valid_release, genre_map)

    assert result["genres"] == ["Thriller"]
    assert "Unknown genre ID: 999999" in caplog.text


def test_normalise_release_converts_null_overview_to_empty_string(
    valid_release,
    genre_map,
):
    valid_release["overview"] = None

    result = normalise_release(valid_release, genre_map)

    assert result["overview"] == ""


def test_transform_releases_processes_valid_releases(
    valid_release,
    genre_map,
):
    raw_payload = {
        "results": [valid_release],
    }

    releases, stats = transform_releases(
        raw_payload,
        genre_map,
    )

    assert len(releases) == 1
    assert releases[0]["tmdb_id"] == 1101412

    assert stats == {
        "retrieved": 1,
        "accepted": 1,
        "rejected": 0,
        "deduplicated": 0,
    }


def test_transform_releases_rejects_invalid_release(
    valid_release,
    genre_map,
):
    valid_release["release_date"] = "banana"

    raw_payload = {
        "results": [valid_release],
    }

    releases, stats = transform_releases(
        raw_payload,
        genre_map,
    )

    assert releases == []

    assert stats == {
        "retrieved": 1,
        "accepted": 0,
        "rejected": 1,
        "deduplicated": 0,
    }


def test_transform_releases_removes_duplicate_tmdb_ids(
    valid_release,
    genre_map,
):
    duplicate_release = valid_release.copy()

    raw_payload = {
        "results": [
            valid_release,
            duplicate_release,
        ],
    }

    releases, stats = transform_releases(
        raw_payload,
        genre_map,
    )

    assert len(releases) == 1
    assert releases[0]["tmdb_id"] == 1101412

    assert stats == {
        "retrieved": 2,
        "accepted": 1,
        "rejected": 0,
        "deduplicated": 1,
    }


def test_transform_releases_handles_empty_results(
    genre_map,
):
    raw_payload = {
        "results": [],
    }

    releases, stats = transform_releases(
        raw_payload,
        genre_map,
    )

    assert releases == []

    assert stats == {
        "retrieved": 0,
        "accepted": 0,
        "rejected": 0,
        "deduplicated": 0,
    }


def test_build_cache_response_returns_api_ready_payload():
    releases = [
        {
            "tmdb_id": 1101412,
            "title": "Fall 2: Deadpoint",
            "release_date": "2026-09-09",
            "original_language": "en",
            "overview": "A film synopsis.",
            "popularity": 51.7971,
            "genres": ["Thriller"],
        }
    ]

    result = build_cache_response(
        releases,
        region="GB",
    )

    assert result["region"] == "GB"
    assert result["release_count"] == 1
    assert result["releases"] == releases
    assert "generated_at" in result
    generated_at = datetime.fromisoformat(result["generated_at"])
    assert generated_at.tzinfo is not None


def test_build_cache_response_handles_no_releases():
    result = build_cache_response(
        [],
        region="GB",
    )

    assert result["region"] == "GB"
    assert result["release_count"] == 0
    assert result["releases"] == []


def test_tmdb_fixtures_can_be_transformed_into_cache_response():
    fixture_directory = Path(__file__).resolve().parent / "fixtures"

    with (fixture_directory / "tmdb_upcoming_page_1.json").open(
        encoding="utf-8"
    ) as release_file:
        raw_payload = json.load(release_file)

    with (fixture_directory / "tmdb_movie_genres.json").open(
        encoding="utf-8"
    ) as genre_file:
        genre_payload = json.load(genre_file)

    genre_map = build_genre_map(genre_payload)

    releases, stats = transform_releases(
        raw_payload,
        genre_map,
    )

    cache_response = build_cache_response(
        releases,
        region="GB",
    )

    assert cache_response["region"] == "GB"
    assert cache_response["release_count"] == len(releases)
    assert cache_response["releases"] == releases
    assert stats["retrieved"] == len(raw_payload["results"])

    assert (
        stats["retrieved"]
        == stats["accepted"] + stats["rejected"] + stats["deduplicated"]
    )

    required_cache_fields = {
        "tmdb_id",
        "title",
        "release_date",
        "original_language",
        "overview",
        "popularity",
        "genres",
    }

    for release in cache_response["releases"]:
        assert required_cache_fields.issubset(release)
