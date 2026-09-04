import json

import pytest

from reelops.storage import (
    read_cache_response,
    save_cache_response,
)


@pytest.fixture
def cache_response():
    return {
        "region": "GB",
        "release_count": 1,
        "generated_at": "2026-09-04T08:00:00+00:00",
        "releases": [
            {
                "tmdb_id": 1101412,
                "title": "Fall 2: Deadpoint",
                "release_date": "2026-09-09",
                "original_language": "en",
                "overview": "A film synopsis.",
                "popularity": 51.7971,
                "genres": ["Thriller"],
            }
        ],
    }


def test_save_cache_response_creates_file_and_parent_directories(
    tmp_path,
    cache_response,
):
    cache_path = tmp_path / "data" / "api-cache" / "latest_upcoming_releases.json"

    returned_path = save_cache_response(
        cache_response,
        cache_path,
    )

    assert returned_path == cache_path
    assert cache_path.exists()

    with cache_path.open(encoding="utf-8") as cache_file:
        saved_payload = json.load(cache_file)

    assert saved_payload == cache_response


def test_read_cache_response_returns_saved_payload(
    tmp_path,
    cache_response,
):
    cache_path = tmp_path / "cache.json"

    save_cache_response(cache_response, cache_path)
    result = read_cache_response(cache_path)

    assert result == cache_response


def test_read_cache_response_raises_when_file_does_not_exist(
    tmp_path,
):
    missing_path = tmp_path / "missing.json"

    with pytest.raises(FileNotFoundError):
        read_cache_response(missing_path)


def test_read_cache_response_raises_for_malformed_json(
    tmp_path,
):
    cache_path = tmp_path / "invalid.json"
    cache_path.write_text(
        "{this is not valid JSON",
        encoding="utf-8",
    )

    with pytest.raises(json.JSONDecodeError):
        read_cache_response(cache_path)
