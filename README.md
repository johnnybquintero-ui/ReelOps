# ReelOps

A film-release explorer using Python Azure Functions and a vanilla JavaScript frontend. Compare REST and GraphQL requests against the same saved TMDb release data.

## Run locally

With your Python environment configured and release cache generated, start each service in a separate terminal.

**1. Local storage**
```bash
npx --yes azurite --silent --location /tmp/reelops-azurite
```

**2. Python API — from the project root**
```bash
source .venv/bin/activate
func start --cors http://localhost:5500
```

**3. Frontend — from the project root**
```bash
python -m http.server 5500 --directory frontend
```

Open http://localhost:5500. Choose REST or GraphQL, optionally enter a year/month, and load releases.

## API

### `GET /api/releases`

Returns upcoming UK releases from the saved cache.

Optional filters:

- `year`: Release year.
- `month`: Release month, from `1` to `12`.

Examples:
```text
/api/releases
/api/releases?year=2026
/api/releases?year=2026&month=10
```

Example response:
```json
{
  "region": "GB",
  "release_count": 1,
  "generated_at": "2026-09-04T09:34:15+00:00",
  "filters": {
    "year": null,
    "month": null
  },
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

Responses:

- `200`: Success; `releases` may be empty.
- `400`: Invalid year or month.
- `503`: Release cache is missing or unreadable.

### `POST /api/graphql`

Returns selected release fields using the same cache and filters.

Send a JSON body:
```json
{
  "query": "query Releases($year: Int, $month: Int) { releases(year: $year, month: $month) { tmdbId title releaseDate genres } }",
  "variables": {
    "year": 2026,
    "month": 10
  }
}
```

Results appear under `data.releases`. Check the `errors` field even when the HTTP status is `200`.

### `GET /api/health`

Checks that the TMDb token is configured and the cache can be read. Returns `200` when healthy, otherwise `503`.

## Data model

REST uses the names below; GraphQL uses camelCase, such as `tmdbId` and `releaseDate`.

| Field | Type | Description |
|---|---|---|
| `tmdb_id` | Integer | Unique positive TMDb identifier |
| `title` | String | Display title |
| `release_date` | Date string | `YYYY-MM-DD` |
| `original_language` | String | Original-language code |
| `overview` | String | Synopsis; may be empty |
| `popularity` | Number or null | TMDb popularity score |
| `genres` | List of strings | Genre names; may be empty |

## Data-quality rules

- Source records require `id`, `title`, `release_date` and `original_language`.
- IDs must be positive integers and are renamed to `tmdb_id`.
- Required strings are trimmed and must be non-empty.
- Release dates must be valid and use `YYYY-MM-DD`.
- Invalid records and duplicate TMDb IDs are excluded.
- Missing or invalid popularity becomes `null`.
- Missing or invalid overview becomes an empty string.
- Genre IDs are mapped to names; unknown IDs are logged and omitted.
- Missing genres become an empty list.
- Counts satisfy: `retrieved = accepted + rejected + deduplicated`.

## Tests

Run from the project root:
```bash
python -m pytest
npm test
```

## Current scope

Uses page 1 of TMDb's upcoming UK releases. Azure deployment and Fabric reporting are the next planned stages.