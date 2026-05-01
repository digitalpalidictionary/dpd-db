#!/usr/bin/env python3
"""Fetch the audio index TSV from the latest dpd-audio release.

Used by CI: the build pipeline only needs the small TSV (lemma_clean +
presence flags), not the 1 GB sqlite tarball. Exits non-zero on any failure
so the workflow fails fast instead of silently producing a corrupt build.
"""

import sys

import requests

from tools.paths import ProjectPaths
from tools.printer import printer as pr

pth = ProjectPaths()

RELEASES_URL = (
    "https://api.github.com/repos/digitalpalidictionary/dpd-audio/releases/latest"
)


def fail(msg: str) -> "None":
    pr.red(msg)
    sys.exit(1)


def get_latest_release() -> dict:
    pr.green_tmr("fetching latest GitHub release")
    headers = {"Accept": "application/vnd.github.v3+json"}
    try:
        response = requests.get(RELEASES_URL, headers=headers, timeout=30)
        response.raise_for_status()
        info = response.json()
        pr.yes("ok")
        return info
    except requests.exceptions.RequestException as e:
        pr.no("failed")
        fail(f"Error fetching latest release: {e}")
        return {}  # unreachable


def find_index_asset(release_info: dict) -> dict:
    pr.green_tmr("finding index tsv")
    for asset in release_info.get("assets", []):
        name = asset["name"]
        if name.startswith("dpd_audio_index_") and name.endswith(".tsv"):
            pr.yes("ok")
            return asset

    pr.no("failed")
    fail("no index tsv asset found in latest release")
    return {}  # unreachable


def download_index(asset: dict) -> None:
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


def main() -> None:
    pr.tic()
    pr.yellow_title("download audio index tsv")
    release_info = get_latest_release()
    asset = find_index_asset(release_info)
    download_index(asset)
    pr.toc()


if __name__ == "__main__":
    main()
