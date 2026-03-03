"""Contributor update script for DPD.

Updates the contributor environment:
1. git pull latest code
2. uv sync dependencies
3. Download latest dpd.db if a newer version is available
"""

import subprocess
from pathlib import Path

import requests

from tools.configger import config_read
from tools.printer import printer as pr

GITHUB_RELEASES_URL = (
    "https://api.github.com/repos/digitalpalidictionary/dpd-db/releases/latest"
)


def pull_latest_code(project_root: Path) -> tuple[bool, str]:
    """Pull the latest code from the remote repository."""
    result = subprocess.run(
        ["git", "pull", "--rebase"],
        cwd=project_root,
        capture_output=True,
        text=True,
        timeout=60,
    )
    if result.returncode == 0:
        return True, result.stdout.strip()
    return False, result.stderr.strip()


def sync_dependencies(project_root: Path) -> bool:
    """Run uv sync to update dependencies."""
    try:
        result = subprocess.run(
            ["uv", "sync"],
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=120,
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def check_db_update_available(
    current_version: str,
) -> tuple[bool, str | None]:
    """Check if a newer database version is available on GitHub Releases."""
    headers = {"Accept": "application/vnd.github.v3+json"}
    try:
        response = requests.get(GITHUB_RELEASES_URL, headers=headers, timeout=30)
        response.raise_for_status()
        release_info = response.json()

        latest_version = release_info.get("tag_name", "")
        if latest_version == current_version:
            return False, None

        for asset in release_info.get("assets", []):
            if "dpd.db" in asset["name"]:
                return True, asset["browser_download_url"]

        return False, None
    except requests.exceptions.RequestException:
        return False, None


def update_environment(project_root: Path) -> str:
    """Run the full update process and return a summary."""
    summary_parts: list[str] = []

    pr.title("DPD Contributor Update")

    # Step 1: Pull latest code
    pr.green("pulling latest code")
    pull_ok, pull_msg = pull_latest_code(project_root)
    if pull_ok:
        pr.yes("ok")
        summary_parts.append(f"Code pull: {pull_msg}")
    else:
        pr.no("failed")
        pr.red(pull_msg)
        summary_parts.append(f"Code pull failed: {pull_msg}")

    # Step 2: Sync dependencies
    pr.green("syncing dependencies")
    if sync_dependencies(project_root):
        pr.yes("ok")
        summary_parts.append("Dependencies: up to date")
    else:
        pr.no("failed")
        summary_parts.append("Dependencies: sync failed")

    # Step 3: Check for database update
    pr.green("checking for database update")
    current_version = config_read("version", "version", default_value="")
    db_available, db_url = check_db_update_available(current_version or "")
    if db_available and db_url:
        pr.yes("new")
        pr.info(f"  New database version available: {db_url}")
        summary_parts.append(
            "Database: new version available (download manually or re-run setup)"
        )
    else:
        pr.yes("ok")
        summary_parts.append("Database: up to date")

    pr.green_title("Update complete!")

    return "\n".join(summary_parts)


if __name__ == "__main__":
    update_environment(Path.cwd())
