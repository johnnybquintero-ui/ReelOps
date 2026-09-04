from unittest.mock import Mock

import pytest
import requests

from reelops.pipeline import refresh_release_cache


def test_refresh_release_cache_runs_complete_pipeline(
    monkeypatch,
    tmp_path,
):
    raw_payload = {
        "results": [
            {
                "id": 1101412,
                "title": "Fall 2: Deadpoint",
                "release_date": "2026-09-09",
                "original_language": "en",
                "genre_ids": [53],
            }
        ]
    }

    genre_payload = {
        "genres": [
            {
                "id": 53,
                "name": "Thriller",
            }
        ]
    }

    genre_map = {
        53: "Thriller",
    }

    releases = [
        {
            "tmdb_id": 1101412,
            "title": "Fall 2: Deadpoint",
            "release_date": "2026-09-09",
            "original_language": "en",
            "overview": "",
            "popularity": None,
            "genres": ["Thriller"],
        }
    ]

    stats = {
        "retrieved": 1,
        "accepted": 1,
        "rejected": 0,
        "deduplicated": 0,
    }

    cache_response = {
        "region": "GB",
        "release_count": 1,
        "generated_at": "2026-09-04T08:00:00+00:00",
        "releases": releases,
    }

    mock_fetch_releases = Mock(return_value=raw_payload)
    mock_fetch_genres = Mock(return_value=genre_payload)
    mock_save_raw = Mock()
    mock_build_genre_map = Mock(return_value=genre_map)
    mock_transform = Mock(return_value=(releases, stats))
    mock_build_cache = Mock(return_value=cache_response)
    mock_save_cache = Mock()

    monkeypatch.setattr(
        "reelops.pipeline.fetch_tmdb_upcoming_releases",
        mock_fetch_releases,
    )
    monkeypatch.setattr(
        "reelops.pipeline.fetch_tmdb_genres",
        mock_fetch_genres,
    )
    monkeypatch.setattr(
        "reelops.pipeline.save_raw_payload_to_bronze",
        mock_save_raw,
    )
    monkeypatch.setattr(
        "reelops.pipeline.build_genre_map",
        mock_build_genre_map,
    )
    monkeypatch.setattr(
        "reelops.pipeline.transform_releases",
        mock_transform,
    )
    monkeypatch.setattr(
        "reelops.pipeline.build_cache_response",
        mock_build_cache,
    )
    monkeypatch.setattr(
        "reelops.pipeline.save_cache_response",
        mock_save_cache,
    )

    result = refresh_release_cache(
        tmdb_base_url="https://api.themoviedb.org/3",
        tmdb_read_token="test-token",
        region="GB",
        page=1,
        data_root=tmp_path,
    )

    assert result == stats

    mock_fetch_releases.assert_called_once_with(
        "https://api.themoviedb.org/3/movie/upcoming",
        "test-token",
        "GB",
        1,
    )
    mock_fetch_genres.assert_called_once_with(
        "https://api.themoviedb.org/3",
        "test-token",
    )

    mock_build_genre_map.assert_called_once_with(genre_payload)
    mock_transform.assert_called_once_with(raw_payload, genre_map)
    mock_build_cache.assert_called_once_with(releases, "GB")

    mock_save_cache.assert_called_once_with(
        cache_response,
        tmp_path / "api-cache" / "latest_upcoming_releases.json",
    )

    mock_save_raw.assert_called_once()

    saved_payload, snapshot_path = mock_save_raw.call_args.args

    assert saved_payload == raw_payload
    assert snapshot_path.name == "page_1.json"
    assert snapshot_path.parent.name.startswith("run_id=")
    assert snapshot_path.parent.parent.name.startswith("extract_date=")


def test_refresh_release_cache_does_not_write_when_fetch_fails(
    monkeypatch,
    tmp_path,
):
    mock_fetch_releases = Mock(side_effect=requests.Timeout("TMDb timed out"))
    mock_save_raw = Mock()
    mock_save_cache = Mock()

    monkeypatch.setattr(
        "reelops.pipeline.fetch_tmdb_upcoming_releases",
        mock_fetch_releases,
    )
    monkeypatch.setattr(
        "reelops.pipeline.save_raw_payload_to_bronze",
        mock_save_raw,
    )
    monkeypatch.setattr(
        "reelops.pipeline.save_cache_response",
        mock_save_cache,
    )

    with pytest.raises(requests.Timeout):
        refresh_release_cache(
            tmdb_base_url="https://api.themoviedb.org/3",
            tmdb_read_token="test-token",
            data_root=tmp_path,
        )

    mock_save_raw.assert_not_called()
    mock_save_cache.assert_not_called()
