"""Shared helpers for the GitHub REST API."""

import os


def github_headers() -> dict[str, str]:
    """Standard API headers, authenticated when a token is in the environment.

    Unauthenticated requests are capped at 60 per hour per IP address, and
    GitHub Actions runners share their IPs across all of GitHub, so CI hits the
    cap through no fault of ours. Authenticated requests get 5000 per hour.
    Local runs without a token keep working on the unauthenticated allowance.
    """
    headers = {"Accept": "application/vnd.github.v3+json"}
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers
