import azure.functions as func
import pytest


@pytest.fixture
def request_factory():
    """Create HTTP requests for Azure Function adapter tests."""

    def make_request(
        params: dict[str, str] | None = None,
    ) -> func.HttpRequest:
        return func.HttpRequest(
            method="GET",
            url="http://localhost:7071/api/releases",
            params=params or {},
            body=b"",
        )

    return make_request
