## Planned MVP API contract

### `GET /api/releases`

Returns upcoming UK film releases from the curated ReelOps cache.

Optional query parameters:

- `year`: Release year, e.g. `2026`
- `month`: Release month from `1` to `12`

Examples:

```text
/api/releases
/api/releases?year=2026
/api/releases?year=2026&month=10
```

### Response

```json
{
  "region": "GB",
  "release_count": 1,
  "generated_at": "2026-09-04T09:34:15+00:00",
  "releases": [
    {
      "tmdb_id": 1101412,
      "title": "Fall 2: Deadpoint",
      "release_date": "2026-09-09",
      "original_language": "en",
      "overview": "A film synopsis.",
      "popularity": 51.7971,
      "genres": ["Thriller"]
    }
  ]
}
```

### HTTP responses

- `200`: Request succeeded; `releases` may be empty
- `400`: Invalid year or month
- `500`: Unexpected server error

## MVP data model

| Field | Type | Description |
|---|---|---|
| `tmdb_id` | Integer | Unique positive TMDb identifier |
| `title` | String | Display title |
| `release_date` | Date string | Date in `YYYY-MM-DD` format |
| `original_language` | String | Original-language code |
| `overview` | String | Synopsis; may be empty |
| `popularity` | Number or null | TMDb popularity score |
| `genres` | List of strings | genres; may be empty |

## Data-quality rules

- `id`, `title`, `release_date` and `original_language` are required in the source.
- `id` must be a positive integer and is renamed to `tmdb_id`.
- Required strings must be non-empty.
- String fields are stripped of surrounding whitespace.
- `release_date` must be a valid date in exact `YYYY-MM-DD` format.
- Invalid records are excluded from the curated output.
- Duplicate TMDb IDs are removed.
- Missing or invalid `popularity` becomes `null`.
- Missing, null or invalid `overview` becomes an empty string.
- Genre IDs are mapped to human-readable names.
- Unknown genre IDs are logged and omitted.
- Missing genres become an empty list.
- The pipeline records retrieved, accepted, rejected and deduplicated counts.
- `retrieved = accepted + rejected + deduplicated`.