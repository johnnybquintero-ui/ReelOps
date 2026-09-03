## MVP API contract

GET /api/releases

Returns upcoming film releases held in the curated ReelOps dataset.

Optional query parameters:
- year: release year, e.g. 2026
- month: release month (1–12), e.g. 10

Examples:
- /api/releases
- /api/releases?year=2026&month=10

Response fields:
- tmdb_id
- title
- release_date
- popularity
- original_language
- fetched_at

Responses:
- 200: matching releases returned
- 400: invalid year or month
- 404: no matching releases
- 500: unexpected server error

## MVP data model

A valid release record contains:

| Field | Type | Required | Description |
|---|---|---:|---|
| `tmdb_id` | Integer | Yes | Unique TMDb movie identifier |
| `title` | String | Yes | Display title supplied by TMDb |
| `release_date` | Date string | Yes | TMDb release date in `YYYY-MM-DD` format |
| `original_language` | String | Yes | Original-language code, such as `en` |
| `overview` | String | No | Film synopsis; may be empty |
| `popularity` | Number | No | TMDb popularity score |
| `genres` | List of strings | No | Human-readable genres mapped from TMDb genre IDs |

## Data-quality rules

- `tmdb_id`, `title`, `release_date` and `original_language` must be present.
- `tmdb_id` must be a positive integer.
- `title` and `original_language` must be non-empty strings.
- `release_date` must be a valid date in `YYYY-MM-DD` format.
- Records missing a valid release date are excluded from the curated MVP output.
- Duplicate `tmdb_id` values are removed.
- `popularity` must be numeric when present; otherwise it is stored as null.
- `overview` may be empty and does not cause the record to be rejected.
- The pipeline records how many records were retrieved, accepted, rejected and deduplicated.
- TMDb `genre_ids` are mapped to human-readable genre names.
- Unknown genre IDs are logged rather than silently discarded.
- A release may have an empty genre list.