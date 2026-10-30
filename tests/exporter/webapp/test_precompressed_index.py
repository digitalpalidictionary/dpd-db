"""Real static mount, middleware, sidecar publication and conditional requests."""

import gzip
import json
from pathlib import Path

import brotli
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from starlette.middleware.gzip import GZipMiddleware

from exporter.webapp.precompressed_index import IndexStaticFiles, publish_index


@pytest.fixture
def setup_index(tmp_path: Path) -> tuple[Path, bytes, TestClient]:
    path = tmp_path / "search_index.json"
    data = json.dumps(["dhamma|धम्म"] * 500).encode()
    publish_index(path, data)
    app = FastAPI()
    app.add_middleware(GZipMiddleware, minimum_size=500)
    app.mount("/static", IndexStaticFiles(directory=tmp_path))
    return path, data, TestClient(app)


@pytest.mark.parametrize(
    ("offer", "encoding"),
    [
        ("br,gzip", "br"),
        ("br;q=0,gzip", "gzip"),
        ("gzip", "gzip"),
        ("xbr", None),
        ("identity", None),
    ],
)
def test_get_head_validators(
    setup_index: tuple[Path, bytes, TestClient], offer: str, encoding: str | None
) -> None:
    path, data, client = setup_index
    url = "/static/search_index.json?v=mutable"
    headers = {"Accept-Encoding": offer}
    response = client.get(url, headers=headers)
    assert response.content == data
    assert response.headers.get("content-encoding") == encoding
    assert response.headers["content-type"] == "application/json"
    assert "cache-control" not in response.headers
    assert "Accept-Encoding" in response.headers["vary"]
    head = client.head(url, headers=headers)
    assert head.content == b""
    assert head.headers["content-length"] == response.headers["content-length"]
    assert head.headers["etag"] == response.headers["etag"]
    cached = client.get(
        url, headers={**headers, "If-None-Match": response.headers["etag"]}
    )
    assert cached.status_code == 304
    assert cached.content == b""
    assert "Accept-Encoding" in cached.headers["vary"]
    # Like the uncompressed file, every representation has a Last-Modified,
    # which browsers use for heuristic freshness and If-Modified-Since.
    since = client.get(
        url,
        headers={**headers, "If-Modified-Since": response.headers["last-modified"]},
    )
    assert since.status_code == 304
    if encoding:
        assert (
            int(response.headers["content-length"])
            == Path(f"{path}.{encoding}").stat().st_size
        )
        other = client.get(
            url,
            headers={
                "Accept-Encoding": "identity",
                "If-None-Match": response.headers["etag"],
            },
        )
        assert other.status_code == 200


@pytest.mark.parametrize(
    "damage", ["missing", "stale", "corrupt", "manifest", "source"]
)
def test_fallback_and_rebuild(
    setup_index: tuple[Path, bytes, TestClient], damage: str
) -> None:
    path, data, client = setup_index
    if damage == "missing":
        Path(f"{path}.br").unlink()
        Path(f"{path}.gzip").unlink()
    elif damage == "stale":
        publish_index(path, b'["old"]')
        path.write_bytes(data)
    elif damage == "corrupt":
        Path(f"{path}.br").write_bytes(b"bad")
        Path(f"{path}.gzip").write_bytes(b"bad")
    elif damage == "manifest":
        Path(f"{path}.encodings.json").write_text("[]", encoding="utf-8")
    else:
        data = b'["changed"]'
        path.write_bytes(data)
    response = client.get(
        "/static/search_index.json", headers={"Accept-Encoding": "br,gzip"}
    )
    assert response.content == data
    assert response.headers.get("content-encoding") != "br"
    publish_index(path, data)
    response = client.get(
        "/static/search_index.json", headers={"Accept-Encoding": "br,gzip"}
    )
    assert response.content == data
    assert response.headers["content-encoding"] == "br"
    assert brotli.decompress(Path(f"{path}.br").read_bytes()) == data
    assert gzip.decompress(Path(f"{path}.gzip").read_bytes()) == data


def test_other_files_errors_and_range(
    setup_index: tuple[Path, bytes, TestClient],
) -> None:
    path, _, client = setup_index
    (path.parent / "other.json").write_text("{}")
    response = client.get("/static/other.json")
    assert response.content == b"{}"
    assert "cache-control" not in response.headers
    assert client.get("/static/missing").status_code == 404
    assert client.post("/static/search_index.json").status_code == 405
    response = client.get(
        "/static/search_index.json",
        headers={"Range": "bytes=0-9", "Accept-Encoding": "identity"},
    )
    assert response.status_code == 206
    assert len(response.content) == 10
