import azure.functions as func
import pytest


@pytest.fixture
def request_factory():
    """Create HTTP requests for Azure Function adapter tests."""

    def make_request(
        params: dict[str, str] | None = None,
        route: str = "releases",
    ) -> func.HttpRequest:
        return func.HttpRequest(
            method="GET",
            url=f"http://localhost:7071/api/{route}",
            params=params or {},
            body=b"",
        )

    return make_request
