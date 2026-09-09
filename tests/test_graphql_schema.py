import pytest

from reelops.graphql_schema import schema


@pytest.fixture
def cache():
    """Provide cached releases to GraphQL through its context."""

    return {
        "releases": [
            {
                "tmdb_id": 1,
                "title": "September Film",
                "release_date": "2026-09-09",
                "original_language": "en",
                "overview": "An example.",
                "popularity": 10.5,
                "genres": ["Thriller"],
            },
            {
                "tmdb_id": 2,
                "title": "October Film",
                "release_date": "2026-10-02",
                "original_language": "en",
                "overview": "Another example.",
                "popularity": 8.0,
                "genres": ["Drama"],
            },
            {
                "tmdb_id": 3,
                "title": "September Film 2027",
                "release_date": "2027-09-03",
                "original_language": "en",
                "overview": "A future example.",
                "popularity": 7.0,
                "genres": ["Science Fiction"],
            },
        ]
    }


def test_graphql_releases_returns_all_releases_without_filters(
    cache,
):
    # Arrange
    query = """
        query {
          releases {
            tmdbId
            title
          }
        }
    """

    # Act
    result = schema.execute_sync(
        query,
        context_value={"cache": cache},
    )

    # Assert
    assert result.errors is None
    assert result.data == {
        "releases": [
            {
                "tmdbId": 1,
                "title": "September Film",
            },
            {
                "tmdbId": 2,
                "title": "October Film",
            },
            {
                "tmdbId": 3,
                "title": "September Film 2027",
            },
        ]
    }


def test_graphql_releases_filters_by_month(
    cache,
):
    # Arrange
    query = """
        query Releases($month: Int) {
          releases(month: $month) {
            title
            releaseDate
          }
        }
    """

    # Act
    result = schema.execute_sync(
        query,
        variable_values={
            "month": 9,
        },
        context_value={"cache": cache},
    )

    # Assert
    assert result.errors is None
    assert result.data == {
        "releases": [
            {
                "title": "September Film",
                "releaseDate": "2026-09-09",
            },
            {
                "title": "September Film 2027",
                "releaseDate": "2027-09-03",
            },
        ]
    }


def test_graphql_releases_filters_by_year_and_month(
    cache,
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

    # Act
    result = schema.execute_sync(
        query,
        variable_values={
            "year": 2026,
            "month": 9,
        },
        context_value={"cache": cache},
    )

    # Assert
    assert result.errors is None
    assert result.data == {
        "releases": [
            {
                "title": "September Film",
                "releaseDate": "2026-09-09",
            }
        ]
    }


def test_graphql_releases_returns_error_for_invalid_month(
    cache,
):
    # Arrange
    query = """
        query Releases($month: Int) {
          releases(month: $month) {
            title
          }
        }
    """

    # Act
    result = schema.execute_sync(
        query,
        variable_values={
            "month": 15,
        },
        context_value={"cache": cache},
    )

    # Assert
    assert result.errors is not None
    assert len(result.errors) == 1
    assert result.errors[0].message == "month must be between 1 and 12"
    assert result.data is None


def test_graphql_releases_returns_only_requested_fields(
    cache,
):
    # Arrange
    query = """
        query {
          releases(year: 2026) {
            title
          }
        }
    """

    # Act
    result = schema.execute_sync(
        query,
        context_value={"cache": cache},
    )

    # Assert
    assert result.errors is None
    assert result.data == {
        "releases": [
            {
                "title": "September Film",
            },
            {
                "title": "October Film",
            },
        ]
    }


def test_graphql_releases_returns_empty_list_when_nothing_matches(
    cache,
):
    # Arrange
    query = """
        query Releases($year: Int) {
          releases(year: $year) {
            title
          }
        }
    """

    # Act
    result = schema.execute_sync(
        query,
        variable_values={
            "year": 2030,
        },
        context_value={"cache": cache},
    )

    # Assert
    assert result.errors is None
    assert result.data == {"releases": []}
