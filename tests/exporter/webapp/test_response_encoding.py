"""Brotli selection and actual upstream gzip fallback interaction."""

import brotli
import pytest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient
from starlette.middleware.gzip import GZipMiddleware
from starlette.responses import JSONResponse

from exporter.webapp.response_encoding import encode_search_response


@pytest.mark.parametrize(
    ("offer", "size", "expected"),
    [
        ("br, gzip", 40000, "br"),
        ("BR;q=0.1, gzip;q=1", 40000, "br"),
        ("br;q=0, gzip", 40000, "gzip"),
        ("xbr, gzip", 40000, "gzip"),
        ("br;q=bogus, gzip", 40000, "gzip"),
        ("br, BR;q=0, gzip", 40000, "gzip"),
        ("br, gzip", 1000, "gzip"),
        ("br, gzip", 1, None),
        ("*;q=0", 40000, None),
        ("br, gzip", 17 * 1024 * 1024, "gzip"),
        ("br", 32757, "br"),  # JSON wrapper adds 11 bytes: exactly 32 KiB
        ("br", 32756, None),
    ],
)
def test_complete_response(offer: str, size: int, expected: str | None) -> None:
    app = FastAPI()
    app.add_middleware(GZipMiddleware, minimum_size=500)

    @app.get("/search_json")
    def search(request: Request) -> JSONResponse:
        return encode_search_response(
            request, JSONResponse({"text": "a" * size}, headers={"Vary": "Origin"})
        )

    with TestClient(app) as client:
        response = client.get("/search_json", headers={"Accept-Encoding": offer})
    assert response.status_code == 200
    assert response.json() == {"text": "a" * size}
    assert response.headers.get("content-encoding") == expected
    assert {"Origin", "Accept-Encoding"} <= set(response.headers["vary"].split(", "))
    assert "cache-control" not in response.headers
    if expected == "br":
        assert int(response.headers["content-length"]) == len(
            brotli.compress(JSONResponse({"text": "a" * size}).body, quality=5)
        )


def test_repeated_headers_and_existing_encoding() -> None:
    request = Request(
        {
            "type": "http",
            "headers": [(b"accept-encoding", b"gzip"), (b"accept-encoding", b"BR")],
        }
    )
    response = JSONResponse({"text": "a" * 40000})
    encode_search_response(request, response)
    assert response.headers["content-encoding"] == "br"
    body = response.body
    encode_search_response(request, response)
    assert response.body == body
