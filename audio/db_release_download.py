#!/usr/bin/env python3
"""
Simple Download Latest Release Script for DPD Audio Database

Downloads the latest GitHub release and extracts the database.
"""

import sqlite3
import sys
import tempfile
from contextlib import closing
from pathlib import Path

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

from audio.github_release import download_index, find_index_asset, get_latest_release
from tools.paths import ProjectPaths
from tools.printer import printer as pr
from tools.tarballer import extract_tarball

pth = ProjectPaths()


def find_archive_asset(release_info):
    """Find the database archive in release assets."""
    pr.green_tmr("finding .tar.gz")
    assets = release_info.get("assets", [])

    for asset in assets:
        name = asset["name"]
        if (
            name.endswith(".tar.gz")
            and name.startswith("dpd_audio_")
            and not name.startswith("dpd_audio_index_")
        ):
            pr.yes("ok")
            return asset

    pr.no("failed")
    pr.red("no archive found")
    return None


def download_archive(asset, work_dir: Path) -> Path | None:
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

    archive_path = work_dir / asset["name"]

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

    pr.green(f"saved to: {archive_path}")
    return archive_path


def install_database(archive_path: Path, work_dir: Path) -> bool:
    """Extract the database, test it has rows, then swap it in for the live one."""

    extract_tarball(archive_path, work_dir, preserve_structure=False)
    new_db = work_dir / pth.dpd_audio_db_path.name

    pr.green_tmr("testing database")
    try:
        with closing(sqlite3.connect(new_db)) as conn:
            rows = conn.execute("SELECT COUNT(*) FROM dpd_audio").fetchone()[0]
    except sqlite3.Error as e:
        pr.no("failed")
        pr.red(f"database test failed: {e}")
        return False
    if rows == 0:
        pr.no("failed")
        pr.red("database has no rows")
        return False
    pr.yes(rows)

    new_db.replace(pth.dpd_audio_db_path)
    pr.green(f"saved to: {pth.dpd_audio_db_path}")
    return True


def main():
    pr.tic()
    pr.yellow_title("download db release")

    release_info = get_latest_release()

    asset = find_archive_asset(release_info)
    if not asset:
        return False

    # Same filesystem as the live db, so the final replace is atomic.
    with tempfile.TemporaryDirectory(dir=pth.dpd_audio_db_path.parent) as tmp:
        work_dir = Path(tmp)
        archive_path = download_archive(asset, work_dir)
        if not archive_path:
            return False
        if not install_database(archive_path, work_dir):
            return False

    download_index(find_index_asset(release_info))

    pr.toc()
    return True


if __name__ == "__main__":
    sys.exit(0 if main() else 1)
