"""Contributor setup script for the Digital Pali Dictionary.

Automates the full environment setup for non-technical contributors:
1. Verify git is installed
2. Initialize only the required submodules
3. Download the latest dpd.db from GitHub Releases
4. Configure contributor username
5. Create a desktop shortcut
6. Print success message
"""

import platform
import shutil
import subprocess
from pathlib import Path

import requests

from tools.configger import config_update
from tools.printer import printer as pr

GITHUB_RELEASES_URL = (
    "https://api.github.com/repos/digitalpalidictionary/dpd-db/releases/latest"
)

REQUIRED_SUBMODULES: list[str] = [
    "resources/sc-data",
    "resources/dpd_submodules",
    "resources/deconstructor_output",
]

SKIPPED_SUBMODULES: list[str] = [
    "resources/dpd_audio",
    "resources/other-dictionaries",
    "resources/tpr_downloads",
    "resources/bw2",
    "resources/fdg_dpd",
    "resources/tipitaka_translation_db",
    "resources/dpd-updater",
    "resources/dpd-updater-go",
]


def check_git() -> tuple[bool, str]:
    """Check if git is installed and functional.

    Returns (is_available, version_string_or_error_message).
    """
    git_path = shutil.which("git")
    if git_path is None:
        return False, get_git_install_instructions()

    try:
        result = subprocess.run(
            [git_path, "--version"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0:
            return True, result.stdout.strip()
        return False, get_git_install_instructions()
    except (subprocess.TimeoutExpired, OSError):
        return False, get_git_install_instructions()


def get_git_install_instructions() -> str:
    """Return OS-specific git installation instructions."""
    system = platform.system()

    if system == "Windows":
        return (
            "Git is not installed. Please install Git for Windows:\n"
            "  Download: https://git-scm.com/download/win\n"
            "  During installation, select "
            "'Git from the command line and also from 3rd-party software'\n"
            "  to ensure git is added to PATH.\n"
            "  Alternatively: winget install Git.Git"
        )
    elif system == "Darwin":
        return (
            "Git is not installed. Install using one of these methods:\n"
            "  Option 1: xcode-select --install\n"
            "  Option 2: brew install git"
        )
    else:
        return (
            "Git is not installed. Install using your package manager:\n"
            "  Debian/Ubuntu:  sudo apt install git\n"
            "  Fedora:         sudo dnf install git\n"
            "  Arch:           sudo pacman -S git"
        )


def get_submodules_to_init() -> list[str]:
    """Return the list of submodules that should be initialized."""
    return list(REQUIRED_SUBMODULES)


def init_submodules(project_root: Path) -> None:
    """Initialize only the required submodules."""
    submodules = get_submodules_to_init()
    for submodule in submodules:
        subprocess.run(
            ["git", "submodule", "update", "--init", "--depth", "1", submodule],
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=300,
        )


def get_latest_db_release_url() -> str | None:
    """Fetch the download URL for dpd.db from the latest GitHub Release."""
    headers = {"Accept": "application/vnd.github.v3+json"}
    try:
        response = requests.get(GITHUB_RELEASES_URL, headers=headers, timeout=30)
        response.raise_for_status()
        release_info = response.json()

        for asset in release_info.get("assets", []):
            if "dpd.db" in asset["name"]:
                return asset["browser_download_url"]

        return None
    except requests.exceptions.RequestException:
        return None


def download_database(url: str, dest: Path) -> bool:
    """Download the database file to the given destination path."""
    try:
        response = requests.get(url, stream=True, timeout=60)
        response.raise_for_status()

        dest.parent.mkdir(parents=True, exist_ok=True)

        with open(dest, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        return True
    except requests.exceptions.RequestException:
        if dest.exists():
            dest.unlink()
        return False


def configure_username(username: str) -> None:
    """Store the contributor username in the project config."""
    username = username.strip()
    if not username:
        raise ValueError("Username cannot be empty")

    config_update("gui2", "username", username, silent=True)


def run_setup(project_root: Path | None = None) -> bool:
    """Run the full contributor setup process."""
    if project_root is None:
        project_root = Path.cwd()

    pr.title("DPD Contributor Setup")

    # Step 1: Check git
    pr.green("checking git installation")
    git_ok, git_msg = check_git()
    if not git_ok:
        pr.no("missing")
        pr.red(git_msg)
        return False
    pr.yes("ok")
    pr.info(f"  {git_msg}")

    # Step 2: Init submodules
    pr.green("initializing required submodules")
    init_submodules(project_root)
    pr.yes("ok")

    # Step 3: Download database
    pr.green("fetching latest database release")
    db_url = get_latest_db_release_url()
    if not db_url:
        pr.no("failed")
        pr.red("Could not find dpd.db in the latest GitHub release.")
        return False
    pr.yes("ok")

    db_dest = project_root / "dpd.db"
    pr.green("downloading database")
    if not download_database(db_url, db_dest):
        pr.no("failed")
        pr.red("Failed to download the database. Check your internet connection.")
        return False
    pr.yes("ok")

    # Step 4: Sync dependencies
    pr.green("installing dependencies")
    try:
        sync_result = subprocess.run(
            ["uv", "sync"],
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=120,
        )
        if sync_result.returncode == 0:
            pr.yes("ok")
        else:
            pr.no("failed")
            pr.red("Failed to install dependencies. Try running 'uv sync' manually.")
            return False
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pr.no("failed")
        pr.red("Could not run 'uv sync'. Make sure uv is installed.")
        return False

    # Step 5: Configure username
    username = input("Enter your contributor username: ").strip()
    if not username:
        pr.red("Username cannot be empty. Please re-run the setup.")
        return False
    configure_username(username)
    pr.info(f"  Username set to: {username}")

    # Step 6: Create desktop shortcut
    pr.green("creating desktop shortcut")
    try:
        from scripts.onboarding.desktop_shortcut import create_desktop_shortcut

        shortcut_path = create_desktop_shortcut(project_root)
        pr.yes("ok")
        pr.info(f"  Shortcut created: {shortcut_path}")
    except Exception as e:
        pr.no("failed")
        pr.warning(f"  Could not create shortcut: {e}")
        pr.info(
            "  You can still launch the GUI with: uv run scripts/onboarding/launch_gui.py"
        )

    pr.green_title("Setup complete!")
    pr.info(
        "You can now launch the GUI by double-clicking the DPD GUI shortcut on your Desktop."
    )

    return True


if __name__ == "__main__":
    run_setup()
