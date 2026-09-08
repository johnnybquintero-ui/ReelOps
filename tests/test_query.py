import pytest

from reelops.query import filter_releases


@pytest.fixture
def releases():
    return [
        {
            "tmdb_id": 1,
            "title": "September 2026",
            "release_date": "2026-09-09",
        },
        {
            "tmdb_id": 2,
            "title": "October 2026",
            "release_date": "2026-10-02",
        },
        {
            "tmdb_id": 3,
            "title": "September 2027",
            "release_date": "2027-09-03",
        },
    ]


def test_filter_releases_returns_all_releases_without_filters(
    releases,
):
    assert filter_releases(releases) == releases


def test_filter_releases_filters_by_year(releases):
    assert (
        filter_releases(
            releases,
            year=2026,
        )
        == releases[:2]
    )


def test_filter_releases_filters_by_month(releases):
    assert filter_releases(
        releases,
        month=9,
    ) == [
        releases[0],
        releases[2],
    ]


def test_filter_releases_filters_by_year_and_month(
    releases,
):
    assert filter_releases(
        releases,
        year=2026,
        month=9,
    ) == [releases[0]]


def test_filter_releases_returns_empty_list_when_nothing_matches(
    releases,
):
    assert (
        filter_releases(
            releases,
            year=2030,
        )
        == []
    )
