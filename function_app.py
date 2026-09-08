import json
import logging
import os
from pathlib import Path
from typing import Any

import azure.functions as func

from reelops.pipeline import refresh_release_cache
from reelops.query import filter_releases, validate_release_filters
from reelops.storage import read_cache_response

# Creates the main Azure Functions application object.
app = func.FunctionApp()

logger = logging.getLogger(__name__)

CACHE_PATH = Path("data/api-cache/latest_upcoming_releases.json")


# Decorator that registers the function as an Azure timer-triggered function
@app.timer_trigger(
    # Refers to an application setting. Locally this comes from local.settings.json;
    # after deployment it comes from the Azure Function App settings.
    schedule="%RELEASE_REFRESH_SCHEDULE%",
    # defines the name of the argument that will receive the timer information
    arg_name="timer",
    # indicates whether the function should run immediately when the application starts
    run_on_startup=False,
    # Persists schedule status so missed executions can be detected after restarts.
    use_monitor=True,
)
def refresh_releases_timer(timer: func.TimerRequest) -> None:
    """Refresh the upcoming-release cache on a schedule."""

    # Check if the timer is past due and log a warning if it is
    if timer.past_due:
        logger.warning("Release refresh timer is running late.")
    # Call the refresh_release_cache function to update the cache and store the returned statistics
    stats = refresh_release_cache(
        tmdb_base_url="https://api.themoviedb.org/3",
        tmdb_read_token=os.environ["TMDB_READ_TOKEN"],
        region="GB",
    )

    logger.info("Scheduled release refresh completed: %s", stats)


def json_response(
    payload: dict[str, Any],
    status_code: int,
) -> func.HttpResponse:
    """Build an explicit JSON HTTP response."""

    return func.HttpResponse(
        body=json.dumps(payload),
        status_code=status_code,
        mimetype="application/json",
    )


@app.route(
    route="releases",
    methods=["GET"],
    auth_level=func.AuthLevel.ANONYMOUS,
)
def get_releases(
    req: func.HttpRequest,
) -> func.HttpResponse:
    """Return cached releases with optional year/month filtering."""

    # Query parameters arrive as strings, for example:
    # {"year": "2026", "month": "9"}.
    year_parameter = req.params.get("year")
    month_parameter = req.params.get("month")

    try:
        # Convert supplied parameters into integers.
        # Missing parameters become None.
        year = int(year_parameter) if year_parameter else None
        month = int(month_parameter) if month_parameter else None

        # Reject out-of-range values before reading the cache.
        validate_release_filters(year, month)

    except ValueError as error:
        # This catches both non-integer input and invalid ranges.
        return json_response(
            {"error": str(error)},
            400,
        )

    try:
        # Only access storage after the request parameters are valid.
        cache = read_cache_response(CACHE_PATH)
    except (FileNotFoundError, json.JSONDecodeError):
        logger.exception("Release cache is unavailable")

        return json_response(
            {"error": "release cache is unavailable"},
            503,
        )

    # The filters have already been validated, so this function
    # only needs to select the matching releases.
    releases = filter_releases(
        cache["releases"],
        year=year,
        month=month,
    )

    # Preserve the cache metadata while replacing the original
    # release list and count with this request's results.
    response = {
        **cache,
        "release_count": len(releases),
        "filters": {
            "year": year,
            "month": month,
        },
        "releases": releases,
    }

    # use json_response helper to convert the response into a JSON HTTP response
    return json_response(response, 200)


@app.route(
    route="health",
    methods=["GET"],
    auth_level=func.AuthLevel.ANONYMOUS,
)
def get_health(
    req: func.HttpRequest,
) -> func.HttpResponse:
    """Return health status of the Function App."""

    try:
        tmdb_token = os.environ["TMDB_READ_TOKEN"]

        if not tmdb_token:
            raise ValueError("TMDB_READ_TOKEN is empty")

    except (KeyError, ValueError) as error:
        logger.error("TMDb token health check failed: %s", error)

        return json_response(
            {"error": ("TMDB_READ_TOKEN is not configured")},
            503,
        )

    try:
        read_cache_response(CACHE_PATH)

    except (FileNotFoundError, json.JSONDecodeError):
        logger.exception("Release cache is unavailable")

        return json_response(
            {"error": ("release cache is unavailable")},
            503,
        )

    return json_response(
        {
            "status": "healthy",
            "checks": {
                "tmdb_token_configured": True,
                "cache_readable": True,
            },
        },
        200,
    )
