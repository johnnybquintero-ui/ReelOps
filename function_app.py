import logging
import os

import azure.functions as func

from reelops.pipeline import refresh_release_cache

# Creates the main Azure Functions application object.
app = func.FunctionApp()

logger = logging.getLogger(__name__)


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
