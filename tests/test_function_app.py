import json
import logging
from unittest.mock import Mock

import pytest

from function_app import get_releases, json_response, refresh_releases_timer


def test_refresh_releases_timer_calls_pipeline(
    monkeypatch,
):
    stats = {
        "retrieved": 1,
        "accepted": 1,
        "rejected": 0,
        "deduplicated": 0,
    }

    mock_refresh = Mock(return_value=stats)

    monkeypatch.setenv(
        "TMDB_READ_TOKEN",
        "test-token",
    )
    monkeypatch.setattr(
        "function_app.refresh_release_cache",
        mock_refresh,
    )

    timer = Mock()
    timer.past_due = False

    result = refresh_releases_timer(timer)

    assert result is None

    mock_refresh.assert_called_once_with(
        tmdb_base_url="https://api.themoviedb.org/3",
        tmdb_read_token="test-token",
        region="GB",
    )


def test_refresh_releases_timer_warns_when_past_due(
    monkeypatch,
    caplog,
):
    monkeypatch.setenv(
        "TMDB_READ_TOKEN",
        "test-token",
    )
    monkeypatch.setattr(
        "function_app.refresh_release_cache",
        Mock(return_value={}),
    )

    timer = Mock()
    timer.past_due = True

    with caplog.at_level(logging.WARNING):
        refresh_releases_timer(timer)

    assert "Release refresh timer is running late." in caplog.text


def test_json_response_builds_json_http_response():
    payload = {
        "status": "healthy",
    }

    response = json_response(payload, status_code=200)

    assert response.status_code == 200
    assert response.mimetype == "application/json"
    assert json.loads(response.get_body()) == payload


@pytest.fixture
def cache_response():
    """Represent the latest release cache read by the endpoint."""

    return {
        "region": "GB",
        "release_count": 2,
        "generated_at": "2026-09-08T10:30:00+00:00",
        "releases": [
            {
                "tmdb_id": 1,
                "title": "September Film",
                "release_date": "2026-09-09",
                "original_language": "en",
                "overview": "First film.",
                "popularity": 20.5,
                "genres": ["Thriller"],
            },
            {
                "tmdb_id": 2,
                "title": "October Film",
                "release_date": "2026-10-15",
                "original_language": "en",
                "overview": "Second film.",
                "popularity": 15.0,
                "genres": ["Drama"],
            },
        ],
    }


def get_response_payload(response):
    """Convert an HTTP response body back into a Python dictionary."""

    return json.loads(response.get_body())


def test_get_releases_returns_complete_cache(
    monkeypatch,
    request_factory,
    cache_response,
):
    # Arrange
    mock_read_cache = Mock(return_value=cache_response)
    mock_filter = Mock(return_value=cache_response["releases"])

    monkeypatch.setattr(
        "function_app.read_cache_response",
        mock_read_cache,
    )
    monkeypatch.setattr(
        "function_app.filter_releases",
        mock_filter,
    )

    request = request_factory()

    # Act
    response = get_releases(request)
    payload = get_response_payload(response)

    # Assert
    assert response.status_code == 200
    assert payload["region"] == "GB"
    assert payload["release_count"] == 2
    assert payload["releases"] == cache_response["releases"]
    assert payload["filters"] == {
        "year": None,
        "month": None,
    }

    mock_read_cache.assert_called_once()
    mock_filter.assert_called_once_with(
        cache_response["releases"],
        year=None,
        month=None,
    )


def test_get_releases_filters_by_year(
    monkeypatch,
    request_factory,
    cache_response,
):
    # Arrange
    matching_releases = cache_response["releases"]

    mock_read_cache = Mock(return_value=cache_response)
    mock_filter = Mock(return_value=matching_releases)

    monkeypatch.setattr(
        "function_app.read_cache_response",
        mock_read_cache,
    )
    monkeypatch.setattr(
        "function_app.filter_releases",
        mock_filter,
    )

    request = request_factory({"year": "2026"})

    # Act
    response = get_releases(request)
    payload = get_response_payload(response)

    # Assert
    assert response.status_code == 200
    assert payload["release_count"] == 2
    assert payload["releases"] == matching_releases
    assert payload["filters"] == {
        "year": 2026,
        "month": None,
    }

    mock_read_cache.assert_called_once()
    mock_filter.assert_called_once_with(
        cache_response["releases"],
        year=2026,
        month=None,
    )


def test_get_releases_filters_by_month(
    monkeypatch,
    request_factory,
    cache_response,
):
    # Arrange
    matching_releases = [cache_response["releases"][0]]

    mock_read_cache = Mock(return_value=cache_response)
    mock_filter = Mock(return_value=matching_releases)

    monkeypatch.setattr(
        "function_app.read_cache_response",
        mock_read_cache,
    )
    monkeypatch.setattr(
        "function_app.filter_releases",
        mock_filter,
    )

    request = request_factory({"month": "9"})

    # Act
    response = get_releases(request)
    payload = get_response_payload(response)

    # Assert
    assert response.status_code == 200
    assert payload["release_count"] == 1
    assert payload["releases"] == matching_releases
    assert payload["filters"] == {
        "year": None,
        "month": 9,
    }

    mock_read_cache.assert_called_once()
    mock_filter.assert_called_once_with(
        cache_response["releases"],
        year=None,
        month=9,
    )


def test_get_releases_filters_by_year_and_month(
    monkeypatch,
    request_factory,
    cache_response,
):
    # Arrange
    matching_releases = [
        cache_response["releases"][0],
    ]

    mock_read_cache = Mock(return_value=cache_response)
    mock_filter = Mock(return_value=matching_releases)

    monkeypatch.setattr(
        "function_app.read_cache_response",
        mock_read_cache,
    )
    monkeypatch.setattr(
        "function_app.filter_releases",
        mock_filter,
    )

    request = request_factory(
        {
            "year": "2026",
            "month": "9",
        }
    )

    # Act
    response = get_releases(request)
    payload = get_response_payload(response)

    # Assert
    assert response.status_code == 200
    assert payload["release_count"] == 1
    assert payload["releases"] == matching_releases
    assert payload["filters"] == {
        "year": 2026,
        "month": 9,
    }

    mock_read_cache.assert_called_once()
    mock_filter.assert_called_once_with(
        cache_response["releases"],
        year=2026,
        month=9,
    )


def test_get_releases_returns_400_for_non_integer_year(
    monkeypatch,
    request_factory,
):
    # Arrange
    mock_read_cache = Mock()
    mock_filter = Mock()

    monkeypatch.setattr(
        "function_app.read_cache_response",
        mock_read_cache,
    )
    monkeypatch.setattr(
        "function_app.filter_releases",
        mock_filter,
    )

    request = request_factory({"year": "hello"})

    # Act
    response = get_releases(request)
    payload = get_response_payload(response)

    # Assert
    assert response.status_code == 400
    assert "error" in payload
    assert "invalid literal for int()" in payload["error"]

    mock_read_cache.assert_not_called()
    mock_filter.assert_not_called()


def test_get_releases_returns_400_for_invalid_month(
    monkeypatch,
    request_factory,
):
    # Arrange
    mock_read_cache = Mock()
    mock_filter = Mock()

    monkeypatch.setattr(
        "function_app.read_cache_response",
        mock_read_cache,
    )
    monkeypatch.setattr(
        "function_app.filter_releases",
        mock_filter,
    )

    request = request_factory({"month": "15"})

    # Act
    response = get_releases(request)
    payload = get_response_payload(response)

    # Assert
    assert response.status_code == 400
    assert payload == {"error": "month must be between 1 and 12"}

    mock_read_cache.assert_not_called()
    mock_filter.assert_not_called()


def test_get_releases_returns_503_when_cache_is_missing(
    monkeypatch,
    request_factory,
):
    # Arrange
    mock_read_cache = Mock(side_effect=FileNotFoundError)
    mock_filter = Mock()

    monkeypatch.setattr(
        "function_app.read_cache_response",
        mock_read_cache,
    )
    monkeypatch.setattr(
        "function_app.filter_releases",
        mock_filter,
    )

    request = request_factory()

    # Act
    response = get_releases(request)
    payload = get_response_payload(response)

    # Assert
    assert response.status_code == 503
    assert payload == {"error": "release cache is unavailable"}

    mock_read_cache.assert_called_once()
    mock_filter.assert_not_called()


def test_get_releases_returns_503_when_cache_is_malformed(
    monkeypatch,
    request_factory,
    caplog,
):
    # Arrange
    json_error = json.JSONDecodeError(
        "Expecting value",
        "",
        0,
    )

    mock_read_cache = Mock(side_effect=json_error)
    mock_filter = Mock()

    monkeypatch.setattr(
        "function_app.read_cache_response",
        mock_read_cache,
    )
    monkeypatch.setattr(
        "function_app.filter_releases",
        mock_filter,
    )

    request = request_factory()

    # Act
    with caplog.at_level(logging.ERROR):
        response = get_releases(request)

    payload = get_response_payload(response)

    # Assert
    assert response.status_code == 503
    assert payload == {"error": "release cache is unavailable"}
    assert "Release cache is unavailable" in caplog.text

    mock_read_cache.assert_called_once()
    mock_filter.assert_not_called()
