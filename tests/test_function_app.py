import logging
from unittest.mock import Mock

from function_app import refresh_releases_timer


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
