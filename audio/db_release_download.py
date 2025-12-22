#!/usr/bin/env python3
"""
Simple Download Latest Release Script for DPD Audio Database

Downloads the latest GitHub release and extracts the database.
"""

import requests
from rich.progress import (
    BarColumn,
    DownloadColumn,
    Progress,
    SpinnerColumn,
    TextColumn,
    TimeRemainingColumn,
    TransferSpeedColumn,
)

from tools.paths import ProjectPaths
from tools.printer import printer as pr
from tools.tarballer import extract_tarball

pth = ProjectPaths()


def get_latest_release():
    """Get latest release information from GitHub."""

    pr.green("fetching latest GitHub release")
    headers = {"Accept": "application/vnd.github.v3+json"}
    try:
        response = requests.get(
            "https://api.github.com/repos/digitalpalidictionary/dpd-audio/releases/latest",
            headers=headers,
            timeout=30,
        )
        response.raise_for_status()
        release_info = response.json()
        pr.yes("ok")
        return release_info
    except requests.exceptions.RequestException as e:
        pr.no("failed")
        pr.red("Error fetching latest release:")
        pr.red(str(e))
        return None


def find_archive_asset(release_info):
    """Find the database archive in release assets."""
    pr.green("finding .tar.gz")
    assets = release_info.get("assets", [])

    for asset in assets:
        if asset["name"].endswith(".tar.gz") and asset["name"].startswith("dpd_audio_"):
            pr.yes("ok")
            return asset

    pr.no("failed")
    pr.red("no archive found")
    return None


def download_archive(asset):
    """Download the release archive."""
    pr.green_title("downloading database")

    response = requests.get(asset["browser_download_url"], stream=True, timeout=30)
    response.raise_for_status()

    # Check if we got an error page instead of the file
    content_type = response.headers.get("content-type", "").lower()
    if "text/html" in content_type:
        pr.red("got HTML page, not file")
        pr.red(f"Content-Type: {content_type}")
        return None

    db_dir = pth.dpd_audio_db_path.parent
    archive_path = db_dir / asset["name"]

    total_size = int(response.headers.get("content-length", 0))

    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            DownloadColumn(),
            TransferSpeedColumn(),
            TimeRemainingColumn(),
        ) as progress:
            task = progress.add_task("", total=total_size)

            with open(archive_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
                    progress.update(task, advance=len(chunk))

    except requests.exceptions.RequestException as e:
        pr.no("failed")
        pr.red(f"Error downloading archive: {e}")
        if archive_path.exists():
            archive_path.unlink()
        return None

    if archive_path.stat().st_size == 0:
        pr.red("empty")
        return None

    # Check if it's actually a tarball
    if archive_path.stat().st_size < 1000:  # Very small file is suspicious
        pr.red("file too small to be a database")
        return None

    pr.info(f"saved to: {archive_path}")
    return archive_path


def extract_database(archive_path):
    """Extract database from archive."""

    db_dir = pth.dpd_audio_db_path.parent
    extract_tarball(archive_path, db_dir, preserve_structure=False)
    pr.info(f"saved to: {pth.dpd_audio_db_path}")
    return True


def main():
    pr.tic()
    pr.title("download db release")

    release_info = get_latest_release()
    if not release_info:
        return False

    asset = find_archive_asset(release_info)
    if not asset:
        return False

    archive_path = download_archive(asset)
    if not archive_path:
        return False

    extract_database(archive_path)

    pr.toc()
    return True


if __name__ == "__main__":
    main()
