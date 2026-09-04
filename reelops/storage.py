import json
from pathlib import Path
from typing import Any


def save_cache_response(
    cache_response: dict[str, Any],
    file_path: Path,
) -> Path:
    """Save a cache response payload to a JSON file."""

    file_path.parent.mkdir(parents=True, exist_ok=True)

    with file_path.open("w", encoding="utf-8") as cache_file:
        json.dump(
            cache_response,
            cache_file,
            ensure_ascii=False,
            indent=4,
        )

    return file_path


def read_cache_response(
    file_path: Path,
) -> dict[str, Any]:
    """Read a cache response payload from a JSON file."""

    with file_path.open("r", encoding="utf-8") as cache_file:
        return json.load(cache_file)
