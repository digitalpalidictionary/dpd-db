"""Fetching the latest dpd-audio release, shared by both audio download scripts."""

import sys
from pathlib import Path
from typing import Any, NoReturn

import requests

from tools.github_api import github_headers
from tools.paths import ProjectPaths
from tools.printer import printer as pr

pth = ProjectPaths()

RELEASES_URL = (
    "https://api.github.com/repos/digitalpalidictionary/dpd-audio/releases/latest"
)


def fail(msg: str) -> NoReturn:
    pr.red(msg)
    sys.exit(1)


def get_latest_release() -> dict[str, Any]:
    """Fetch the latest release metadata from GitHub."""
    pr.green_tmr("fetching latest GitHub release")
    try:
        response = requests.get(RELEASES_URL, headers=github_headers(), timeout=30)
        response.raise_for_status()
        info = response.json()
        pr.yes("ok")
        return info
    except requests.exceptions.RequestException as e:
        pr.no("failed")
        fail(f"Error fetching latest release: {e}")


def find_index_asset(release_info: dict[str, Any]) -> dict[str, Any]:
    """Find the index TSV in the release assets."""
    pr.green_tmr("finding index tsv")
    for asset in release_info.get("assets", []):
        name = asset["name"]
        if name.startswith("dpd_audio_index_") and name.endswith(".tsv"):
            pr.yes("ok")
            return asset

    pr.no("failed")
    fail("no index tsv asset found in latest release")


def download_index(asset: dict[str, Any]) -> Path:
    """Download the index TSV asset to its static path."""
    pr.green_tmr("downloading index tsv")
    try:
        response = requests.get(asset["browser_download_url"], stream=True, timeout=30)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        pr.no("failed")
        fail(f"Error downloading index tsv: {e}")

    target = pth.dpd_audio_index_tsv_path
    target.parent.mkdir(parents=True, exist_ok=True)
    with open(target, "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)

    size = target.stat().st_size
    if size == 0:
        pr.no("failed")
        fail("downloaded index tsv is empty")
    if size < 1000:
        pr.no("failed")
        fail(f"downloaded index tsv is suspiciously small: {size} bytes")

    pr.yes("ok")
    pr.green(f"saved to: {target} ({size} bytes)")
    return target
