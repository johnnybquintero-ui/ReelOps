import json
import logging
from unittest.mock import Mock

import pytest

from function_app import (
    get_health,
    get_releases,
    graphql_api,
    json_response,
    refresh_releases_timer,
)


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


def test_get_health_returns_200_when_token_is_present_and_cache_is_readable(
    monkeypatch,
    request_factory,
):
    # Arrange
    mock_read_cache = Mock()

    monkeypatch.setenv(
        "TMDB_READ_TOKEN",
        "test-token",
    )

    monkeypatch.setattr(
        "function_app.read_cache_response",
        mock_read_cache,
    )

    request = request_factory(route="health")

    # Act
    response = get_health(request)

    payload = get_response_payload(response)

    # Assert
    assert response.status_code == 200
    assert payload["status"] == "healthy"
    assert payload["checks"]["tmdb_token_configured"] is True
    assert payload["checks"]["cache_readable"] is True


def test_get_health_returns_503_when_token_is_missing(
    monkeypatch,
    request_factory,
):
    # Arrange
    mock_read_cache = Mock()

    monkeypatch.delenv(
        "TMDB_READ_TOKEN",
        raising=False,
    )
    monkeypatch.setattr(
        "function_app.read_cache_response",
        mock_read_cache,
    )

    request = request_factory(route="health")

    # Act
    response = get_health(request)
    payload = get_response_payload(response)

    # Assert
    assert response.status_code == 503
    assert payload == {"error": "TMDB_READ_TOKEN is not configured"}
    mock_read_cache.assert_not_called()


def test_get_health_returns_503_when_cache_is_unreadable(
    monkeypatch,
    request_factory,
):
    # Arrange
    mock_read_cache = Mock(side_effect=FileNotFoundError)

    monkeypatch.setenv(
        "TMDB_READ_TOKEN",
        "test-token",
    )
    monkeypatch.setattr(
        "function_app.read_cache_response",
        mock_read_cache,
    )

    request = request_factory(route="health")

    # Act
    response = get_health(request)

    payload = get_response_payload(response)

    # Assert
    assert response.status_code == 503
    assert payload == {"error": "release cache is unavailable"}
    mock_read_cache.assert_called_once()


def test_get_health_returns_503_when_token_is_empty(
    monkeypatch,
    request_factory,
):
    # Arrange
    mock_read_cache = Mock()

    monkeypatch.setenv(
        "TMDB_READ_TOKEN",
        "",
    )
    monkeypatch.setattr(
        "function_app.read_cache_response",
        mock_read_cache,
    )

    request = request_factory(route="health")

    # Act
    response = get_health(request)
    payload = get_response_payload(response)

    # Assert
    assert response.status_code == 503
    assert payload == {"error": "TMDB_READ_TOKEN is not configured"}
    mock_read_cache.assert_not_called()


def test_graphql_api_executes_valid_query_and_variables(
    monkeypatch,
    graphql_request_factory,
    cache_response,
):
    # Arrange
    query = """
        query Releases($year: Int, $month: Int) {
          releases(year: $year, month: $month) {
            title
            releaseDate
          }
        }
    """
    variables = {
        "year": 2026,
        "month": 9,
    }

    graphql_result = Mock(
        data={
            "releases": [
                {
                    "title": "September Film",
                    "releaseDate": "2026-09-09",
                }
            ]
        },
        errors=None,
    )

    mock_read_cache = Mock(return_value=cache_response)
    mock_schema = Mock()
    mock_schema.execute_sync.return_value = graphql_result

    monkeypatch.setattr(
        "function_app.read_cache_response",
        mock_read_cache,
    )
    monkeypatch.setattr(
        "function_app.schema",
        mock_schema,
    )

    request = graphql_request_factory(
        {
            "query": query,
            "variables": variables,
            "operationName": "Releases",
        }
    )

    # Act
    response = graphql_api(request)
    payload = get_response_payload(response)

    # Assert
    assert response.status_code == 200
    assert payload == {
        "data": {
            "releases": [
                {
                    "title": "September Film",
                    "releaseDate": "2026-09-09",
                }
            ]
        }
    }

    mock_read_cache.assert_called_once()
    mock_schema.execute_sync.assert_called_once_with(
        query,
        variable_values=variables,
        operation_name="Releases",
        context_value={"cache": cache_response},
    )


def test_graphql_api_returns_only_selected_fields(
    monkeypatch,
    graphql_request_factory,
    cache_response,
):
    # Arrange
    query = """
        query {
          releases {
            title
          }
        }
    """

    graphql_result = Mock(
        data={
            "releases": [
                {
                    "title": "September Film",
                }
            ]
        },
        errors=None,
    )

    mock_read_cache = Mock(return_value=cache_response)
    mock_schema = Mock()
    mock_schema.execute_sync.return_value = graphql_result

    monkeypatch.setattr(
        "function_app.read_cache_response",
        mock_read_cache,
    )
    monkeypatch.setattr(
        "function_app.schema",
        mock_schema,
    )

    request = graphql_request_factory(
        {
            "query": query,
        }
    )

    # Act
    response = graphql_api(request)
    payload = get_response_payload(response)

    # Assert
    assert response.status_code == 200
    assert payload == {
        "data": {
            "releases": [
                {
                    "title": "September Film",
                }
            ]
        }
    }

    returned_release = payload["data"]["releases"][0]
    assert set(returned_release) == {"title"}

    mock_read_cache.assert_called_once()
    mock_schema.execute_sync.assert_called_once_with(
        query,
        variable_values=None,
        operation_name=None,
        context_value={"cache": cache_response},
    )


def test_graphql_api_returns_400_for_invalid_json(
    monkeypatch,
    graphql_request_factory,
):
    # Arrange
    mock_read_cache = Mock()
    mock_schema = Mock()

    monkeypatch.setattr(
        "function_app.read_cache_response",
        mock_read_cache,
    )
    monkeypatch.setattr(
        "function_app.schema",
        mock_schema,
    )

    request = graphql_request_factory(
        raw_body=b'{"query": invalid}',
    )

    # Act
    response = graphql_api(request)
    payload = get_response_payload(response)

    # Assert
    assert response.status_code == 400
    assert payload == {"error": "request body must be valid JSON"}

    mock_read_cache.assert_not_called()
    mock_schema.execute_sync.assert_not_called()


@pytest.mark.parametrize(
    "request_payload",
    [
        {},
        {"query": ""},
        {"query": "   "},
    ],
    ids=[
        "missing-query",
        "empty-query",
        "whitespace-query",
    ],
)
def test_graphql_api_returns_400_for_missing_or_empty_query(
    monkeypatch,
    graphql_request_factory,
    request_payload,
):
    # Arrange
    mock_read_cache = Mock()
    mock_schema = Mock()

    monkeypatch.setattr(
        "function_app.read_cache_response",
        mock_read_cache,
    )
    monkeypatch.setattr(
        "function_app.schema",
        mock_schema,
    )

    request = graphql_request_factory(request_payload)

    # Act
    response = graphql_api(request)
    payload = get_response_payload(response)

    # Assert
    assert response.status_code == 400
    assert payload == {"error": "query must be a non-empty string"}

    mock_read_cache.assert_not_called()
    mock_schema.execute_sync.assert_not_called()


def test_graphql_api_returns_400_when_body_is_not_an_object(
    monkeypatch,
    graphql_request_factory,
):
    # Arrange
    mock_read_cache = Mock()
    mock_schema = Mock()

    monkeypatch.setattr(
        "function_app.read_cache_response",
        mock_read_cache,
    )
    monkeypatch.setattr(
        "function_app.schema",
        mock_schema,
    )

    request = graphql_request_factory(["not", "an", "object"])

    # Act
    response = graphql_api(request)
    payload = get_response_payload(response)

    # Assert
    assert response.status_code == 400
    assert payload == {"error": "request body must be a JSON object"}

    mock_read_cache.assert_not_called()
    mock_schema.execute_sync.assert_not_called()


@pytest.mark.parametrize(
    "cache_error",
    [
        FileNotFoundError(),
        json.JSONDecodeError(
            "Invalid JSON",
            "",
            0,
        ),
    ],
    ids=[
        "missing-cache",
        "malformed-cache",
    ],
)
def test_graphql_api_returns_503_when_cache_is_unavailable(
    monkeypatch,
    graphql_request_factory,
    cache_error,
):
    # Arrange
    mock_read_cache = Mock(side_effect=cache_error)
    mock_schema = Mock()

    monkeypatch.setattr(
        "function_app.read_cache_response",
        mock_read_cache,
    )
    monkeypatch.setattr(
        "function_app.schema",
        mock_schema,
    )

    request = graphql_request_factory(
        {
            "query": "{ releases { title } }",
        }
    )

    # Act
    response = graphql_api(request)
    payload = get_response_payload(response)

    # Assert
    assert response.status_code == 503
    assert payload == {"error": "release cache is unavailable"}

    mock_read_cache.assert_called_once()
    mock_schema.execute_sync.assert_not_called()


def test_graphql_api_returns_errors_for_invalid_field(
    monkeypatch,
    graphql_request_factory,
    cache_response,
):
    # Arrange
    query = """
        query {
          releases {
            nonexistentField
          }
        }
    """

    graphql_error = Mock(
        message=("Cannot query field " "'nonexistentField' on type 'Release'.")
    )
    graphql_result = Mock(
        data=None,
        errors=[graphql_error],
    )

    mock_read_cache = Mock(return_value=cache_response)
    mock_schema = Mock()
    mock_schema.execute_sync.return_value = graphql_result

    monkeypatch.setattr(
        "function_app.read_cache_response",
        mock_read_cache,
    )
    monkeypatch.setattr(
        "function_app.schema",
        mock_schema,
    )

    request = graphql_request_factory(
        {
            "query": query,
        }
    )

    # Act
    response = graphql_api(request)
    payload = get_response_payload(response)

    # Assert
    assert response.status_code == 200
    assert payload == {
        "errors": [
            {"message": ("Cannot query field " "'nonexistentField' on type 'Release'.")}
        ]
    }

    mock_read_cache.assert_called_once()
    mock_schema.execute_sync.assert_called_once_with(
        query,
        variable_values=None,
        operation_name=None,
        context_value={"cache": cache_response},
    )


def test_graphql_api_returns_errors_for_invalid_month(
    monkeypatch,
    graphql_request_factory,
    cache_response,
):
    # Arrange
    query = """
        query Releases($month: Int) {
          releases(month: $month) {
            title
          }
        }
    """

    graphql_error = Mock(message="month must be between 1 and 12")
    graphql_result = Mock(
        data=None,
        errors=[graphql_error],
    )

    mock_read_cache = Mock(return_value=cache_response)
    mock_schema = Mock()
    mock_schema.execute_sync.return_value = graphql_result

    monkeypatch.setattr(
        "function_app.read_cache_response",
        mock_read_cache,
    )
    monkeypatch.setattr(
        "function_app.schema",
        mock_schema,
    )

    request = graphql_request_factory(
        {
            "query": query,
            "variables": {
                "month": 15,
            },
            "operationName": "Releases",
        }
    )

    # Act
    response = graphql_api(request)
    payload = get_response_payload(response)

    # Assert
    assert response.status_code == 200
    assert payload == {"errors": [{"message": ("month must be between 1 and 12")}]}

    mock_read_cache.assert_called_once()
    mock_schema.execute_sync.assert_called_once_with(
        query,
        variable_values={
            "month": 15,
        },
        operation_name="Releases",
        context_value={"cache": cache_response},
    )
