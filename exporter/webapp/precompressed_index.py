"""Build and serve only the autocomplete index's verified compressed sidecars."""

from email.utils import formatdate
import gzip
import hashlib
import json
import os
from pathlib import Path
from tempfile import NamedTemporaryFile

from anyio import to_thread
import brotli
from starlette.datastructures import Headers
from starlette.responses import Response
from starlette.staticfiles import StaticFiles
from starlette.types import Scope

from exporter.webapp.response_encoding import accepts_encoding


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def atomic_write(path: Path, data: bytes) -> None:
    """Publish each complete file; publish the verification manifest last."""
    with NamedTemporaryFile(dir=path.parent, delete=False) as temporary:
        temporary_path = Path(temporary.name)
        try:
            temporary.write(data)
            temporary.flush()
            os.fchmod(temporary.fileno(), 0o644)
            temporary_path.replace(path)
        finally:
            temporary_path.unlink(missing_ok=True)


def publish_index(path: Path, data: bytes) -> None:
    """Build offline. Interrupted/mixed publication falls back to source JSON."""
    artifacts = {
        "br": brotli.compress(data, quality=11),
        "gzip": gzip.compress(data, compresslevel=9, mtime=0),
    }
    manifest = {"source": digest(data), **{k: digest(v) for k, v in artifacts.items()}}
    atomic_write(path, data)
    for encoding, body in artifacts.items():
        atomic_write(Path(f"{path}.{encoding}"), body)
    atomic_write(Path(f"{path}.encodings.json"), json.dumps(manifest).encode())


class IndexStaticFiles(StaticFiles):
    """Keep all other static URLs and cache policies unchanged."""

    def compressed_response(self, path: str, scope: Scope) -> Response | None:
        request_headers = Headers(scope=scope)
        # Preserve upstream range semantics rather than ranging encoded bytes.
        if "range" in request_headers:
            return None
        encodings = [e for e in ("br", "gzip") if accepts_encoding(request_headers, e)]
        if not encodings:
            return None
        full_path, stat = self.lookup_path(path)
        if stat is None:
            return None
        source = Path(full_path)
        try:
            manifest = json.loads(Path(f"{source}.encodings.json").read_bytes())
            if manifest.get("source") != digest(source.read_bytes()):
                return None
            for encoding in encodings:
                sidecar = Path(f"{source}.{encoding}")
                try:
                    body = sidecar.read_bytes()
                    modified = sidecar.stat().st_mtime
                except OSError:
                    continue
                checksum = digest(body)
                if manifest.get(encoding) != checksum:
                    continue
                headers = {
                    "Content-Encoding": encoding,
                    "Vary": "Accept-Encoding",
                    "ETag": f'"{checksum}"',
                    # The encoded file's own publication time, so browsers keep
                    # the same heuristic freshness as the uncompressed file.
                    "Last-Modified": formatdate(modified, usegmt=True),
                }
                if self.is_not_modified(Headers(headers), request_headers):
                    return Response(status_code=304, headers=headers)
                headers["Content-Length"] = str(len(body))
                return Response(
                    b"" if scope["method"] == "HEAD" else body,
                    media_type="application/json",
                    headers=headers,
                )
        except (OSError, ValueError, AttributeError):
            pass
        return None

    async def get_response(self, path: str, scope: Scope) -> Response:
        if path != "search_index.json" or scope["method"] not in ("GET", "HEAD"):
            return await super().get_response(path, scope)
        response = await to_thread.run_sync(self.compressed_response, path, scope)
        if response is None:
            response = await super().get_response(path, scope)
            response.headers.add_vary_header("Accept-Encoding")
        return response
