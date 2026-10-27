"""Optional bounded Brotli compression in the synchronous search worker."""

import re

import brotli
from starlette.datastructures import Headers
from starlette.requests import Request
from starlette.responses import JSONResponse

BROTLI_MIN_BYTES = 32 * 1024
BROTLI_MAX_BYTES = 16 * 1024 * 1024


def accepts_encoding(headers: Headers, coding: str) -> bool:
    """Recognize explicit nonzero offers only, without ranking encoding preferences."""
    offers = []
    for header in headers.getlist("accept-encoding"):
        for item in header.lower().split(","):
            if item.split(";", 1)[0].strip() != coding:
                continue
            match = re.fullmatch(
                rf"\s*{coding}\s*(?:;\s*q\s*=\s*(0(?:\.\d{{0,3}})?|1(?:\.0{{0,3}})?))?\s*",
                item,
            )
            offers.append(bool(match) and (match[1] is None or float(match[1]) > 0))
    return bool(offers) and all(offers)


def encode_search_response(request: Request, response: JSONResponse) -> JSONResponse:
    # Upstream GZipMiddleware handles every fallback and skips already-encoded
    # responses. Keep large bodies off the additional Brotli allocation path.
    response.headers.add_vary_header("Accept-Encoding")
    if (
        "content-encoding" not in response.headers
        and BROTLI_MIN_BYTES <= len(response.body) <= BROTLI_MAX_BYTES
        and accepts_encoding(request.headers, "br")
    ):
        response.body = brotli.compress(bytes(response.body), quality=5)
        response.headers["Content-Encoding"] = "br"
        response.headers["Content-Length"] = str(len(response.body))
    return response
