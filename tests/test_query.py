import pytest

from reelops.query import filter_releases, validate_release_filters


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


@pytest.mark.parametrize(
    ("year", "month"),
    [
        (2023, 5),
        (2023, None),
        (None, 5),
        (None, None),
    ],
)
def test_validate_release_filters_accepts_valid_filters(
    year,
    month,
):
    validate_release_filters(year=year, month=month)


@pytest.mark.parametrize(
    "invalid_year",
    [
        999,
        10000,
    ],
)
def test_validate_release_filters_rejects_invalid_year(
    invalid_year,
):
    with pytest.raises(
        ValueError,
        match="year must be a four-digit integer",
    ):
        validate_release_filters(
            year=invalid_year,
            month=None,
        )


@pytest.mark.parametrize(
    "invalid_month",
    [
        0,
        13,
    ],
)
def test_validate_release_filters_rejects_invalid_month(
    invalid_month,
):
    with pytest.raises(
        ValueError,
        match="month must be between 1 and 12",
    ):
        validate_release_filters(
            year=None,
            month=invalid_month,
        )


@pytest.mark.parametrize(
    ("year", "month"),
    [
        (1000, 1),
        (9999, 12),
    ],
)
def test_validate_release_filters_accepts_boundary_values(
    year,
    month,
):
    validate_release_filters(year=year, month=month)
