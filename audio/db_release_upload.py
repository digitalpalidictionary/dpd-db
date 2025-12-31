#!/usr/bin/env python3
"""
Release and upload script for DPD Audio Database.
Creates a tarball of the database and uploads it to a new GitHub release.
"""

from datetime import datetime
from pathlib import Path
import sys

# Add the project root to the Python path
sys.path.append(str(Path(__file__).parent.parent.parent))

from github import Github, Auth
from github.GithubException import UnknownObjectException

from tools.configger import config_read, config_test
from tools.printer import printer as pr
from tools.paths import ProjectPaths
from audio.db.db_helpers import make_version

pth = ProjectPaths()


def get_archive_path(version: str) -> Path | None:
    """Get path of existing tarball."""
    archive_name = f"dpd_audio_{version}.tar.gz"
    db_dir = pth.dpd_audio_db_path.parent
    archive_path = db_dir / archive_name

    if not archive_path.exists():
        pr.red(f"Archive not found: {archive_path}")
        pr.red("Please run db_create.py first to generate the archive.")
        return None

    return archive_path


def create_github_release(version: str, archive_path: Path) -> bool:
    """Create GitHub release and upload archive."""
    pr.green_title(f"creating GitHub release {version}")

    github_token = config_read("github", "token")
    if not github_token:
        pr.no("failed")
        pr.red(
            "GitHub token not found in config. Add [github] token = your_token to config file"
        )
        return False

    try:
        auth = Auth.Token(github_token)
        g = Github(auth=auth)
        repo = g.get_repo("digitalpalidictionary/dpd-audio")

        # Check if release already exists
        pr.green("checking existing release")
        try:
            existing_release = repo.get_release(version)
            pr.no("yes")
            pr.green("deleting existing release")
            existing_release.delete_release()
            pr.yes("ok")
        except UnknownObjectException:
            pr.yes("no")

        # Create new release
        pr.green("creating release")
        release = repo.create_git_release(
            tag=version,
            name=f"DPD Audio Database {version}",
            message=f"DPD Audio Database release {version}\n\nBuilt on {datetime.now().isoformat()}",
            draft=False,
            prerelease=False,
        )
        pr.yes("ok")

        # Upload asset
        pr.green("uploading db")
        release.upload_asset(str(archive_path))
        pr.yes("ok")

        return True

    except Exception as e:
        pr.no("failed")
        pr.red(f"Error creating/uploading release: {e}")
        return False


def main():
    pr.tic()
    version = make_version()
    pr.title(f"upload db release {version}")

    if config_test("exporter", "upload_audio_db", "no"):
        pr.green_title("disabled in config.ini")
        pr.toc()
        return

    archive_path = get_archive_path(version)
    if not archive_path:
        return

    # Create GitHub release
    success = create_github_release(version, archive_path)

    if not success:
        pr.red("failed to create release")

    pr.toc()


if __name__ == "__main__":
    main()
