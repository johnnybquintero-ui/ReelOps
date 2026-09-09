import json
from typing import Any

import azure.functions as func
import pytest


@pytest.fixture
def request_factory():
    """Create GET requests for Azure Function adapter tests."""

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


@pytest.fixture
def graphql_request_factory():
    """Create POST requests for the GraphQL HTTP adapter."""

    def make_request(
        payload: Any = None,
        raw_body: bytes | None = None,
    ) -> func.HttpRequest:
        if raw_body is not None:
            body = raw_body
        else:
            body = json.dumps(payload).encode("utf-8")

        return func.HttpRequest(
            method="POST",
            url="http://localhost:7071/api/graphql",
            headers={
                "Content-Type": "application/json",
            },
            params={},
            body=body,
        )

    return make_request
