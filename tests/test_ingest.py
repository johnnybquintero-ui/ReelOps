import json
from pathlib import Path
from unittest.mock import Mock

import pytest
import requests

from reelops.ingest import fetch_tmdb_upcoming_releases, save_raw_payload_to_bronze


def test_fetch_tmdb_upcoming_releases_returns_source_payload(monkeypatch):
    fixture_path = (
        Path(__file__).resolve().parent / "fixtures" / "tmdb_upcoming_page_1.json"
    )

    with fixture_path.open(encoding="utf-8") as fixture_file:
        expected_payload = json.load(fixture_file)

    mock_response = Mock()
    mock_response.json.return_value = expected_payload

    mock_get = Mock(return_value=mock_response)
    monkeypatch.setattr(
        "reelops.ingest.requests.get",
        mock_get,
    )

    result = fetch_tmdb_upcoming_releases(
        "https://example.com/upcoming",
        "test-token",
    )

    assert result == expected_payload

    mock_get.assert_called_once_with(
        "https://example.com/upcoming",
        headers={
            "Authorization": "Bearer test-token",
            "Accept": "application/json",
        },
        timeout=10,
    )

    mock_response.raise_for_status.assert_called_once_with()
    mock_response.json.assert_called_once_with()


def test_fetch_tmdb_upcoming_releases_propagates_http_error(monkeypatch):
    mock_response = Mock()
    mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(
        "400 Client Error"
    )

    mock_get = Mock(return_value=mock_response)
    monkeypatch.setattr(
        "reelops.ingest.requests.get",
        mock_get,
    )

    with pytest.raises(requests.exceptions.HTTPError):
        fetch_tmdb_upcoming_releases(
            "https://example.com/upcoming",
            "test-token",
        )

    mock_response.raise_for_status.assert_called_once_with()
    mock_response.json.assert_not_called()


def test_fetch_tmdb_upcoming_releases_propagates_timeout(monkeypatch):
    mock_get = Mock(side_effect=requests.exceptions.Timeout("Request timed out"))

    monkeypatch.setattr(
        "reelops.ingest.requests.get",
        mock_get,
    )

    with pytest.raises(requests.exceptions.Timeout):
        fetch_tmdb_upcoming_releases(
            "https://example.com/upcoming",
            "test-token",
        )

    mock_get.assert_called_once()


def test_fetch_tmdb_upcoming_releases_propagates_connection_error(
    monkeypatch,
):
    mock_get = Mock(side_effect=requests.exceptions.ConnectionError("Connection error"))

    monkeypatch.setattr(
        "reelops.ingest.requests.get",
        mock_get,
    )

    with pytest.raises(requests.exceptions.ConnectionError):
        fetch_tmdb_upcoming_releases(
            "https://example.com/upcoming",
            "test-token",
        )

    mock_get.assert_called_once()

def test_save_raw_payload_to_bronze_writes_payload_unchanged(
    tmp_path,
):
    raw_payload = {
        "page": 1,
        "results": [
            {
                "id": 1058424,
                "title": "Hope",
                "original_title": "호프",
            }
        ],
    }

    bronze_path = (
        tmp_path
        / "data"
        / "bronze"
        / "tmdb_upcoming_releases.json"
    )

    returned_path = save_raw_payload_to_bronze(
        raw_payload,
        bronze_path,
    )

    assert bronze_path.exists()
    assert returned_path == bronze_path

    with bronze_path.open(encoding="utf-8") as bronze_file:
        saved_payload = json.load(bronze_file)

    assert saved_payload == raw_payload