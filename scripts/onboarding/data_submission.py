"""Data submission via git commit and push for DPD contributors.

Stages contributor data files, creates an auto-generated commit,
and pushes to the remote repository. Handles push rejections by
pulling and retrying.
"""

import subprocess
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from tools.configger import config_read

CONTRIBUTOR_DATA_DIR = "gui2/data"


@dataclass
class SubmissionResult:
    success: bool
    message: str


def get_contributor_data_patterns(username: str) -> list[str]:
    """Return the file patterns for a contributor's data files."""
    return [
        f"{CONTRIBUTOR_DATA_DIR}/additions_{username}.json",
        f"{CONTRIBUTOR_DATA_DIR}/additions_added_{username}.json",
        f"{CONTRIBUTOR_DATA_DIR}/corrections_{username}.json",
        f"{CONTRIBUTOR_DATA_DIR}/corrections_added_{username}.json",
    ]


def find_changed_data_files(project_root: Path, username: str) -> list[str]:
    """Find contributor data files that have been modified."""
    result = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=project_root,
        capture_output=True,
        text=True,
        timeout=30,
    )
    if result.returncode != 0:
        return []

    patterns = get_contributor_data_patterns(username)

    changed: list[str] = []
    for line in result.stdout.rstrip().splitlines():
        filepath = line[3:].strip()
        if any(pattern in filepath for pattern in patterns):
            changed.append(filepath)

    return changed


def build_commit_message(username: str) -> str:
    """Build an auto-generated commit message."""
    date = datetime.now().strftime("%Y-%m-%d")
    return f"contrib({username}): submit data {date}"


def submit_data(project_root: Path) -> SubmissionResult:
    """Stage, commit, and push contributor data files."""
    username = config_read("gui2", "username")
    if not username:
        return SubmissionResult(
            success=False,
            message="No username configured. Please run the setup script first.",
        )

    changed_files = find_changed_data_files(project_root, username)
    if not changed_files:
        return SubmissionResult(
            success=False,
            message="No changes to submit. Your data files have not been modified.",
        )

    for filepath in changed_files:
        subprocess.run(
            ["git", "add", filepath],
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=30,
        )

    commit_msg = build_commit_message(username)
    subprocess.run(
        ["git", "commit", "-m", commit_msg],
        cwd=project_root,
        capture_output=True,
        text=True,
        timeout=30,
    )

    push_result = subprocess.run(
        ["git", "push"],
        cwd=project_root,
        capture_output=True,
        text=True,
        timeout=60,
    )

    if push_result.returncode != 0:
        subprocess.run(
            ["git", "pull", "--rebase"],
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=60,
        )

        retry_result = subprocess.run(
            ["git", "push"],
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=60,
        )

        if retry_result.returncode != 0:
            return SubmissionResult(
                success=False,
                message=(
                    "Failed to push data after retry. "
                    "Please check your internet connection and try again."
                ),
            )

    return SubmissionResult(
        success=True,
        message="Data submitted successfully!",
    )
