"""Tests for contributor setup script.

Tests cover: git detection, selective submodule initialization,
database download from GitHub Releases, contributor username
configuration, and idempotent re-runs.
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from scripts.onboarding.contributor_setup import (
    GITHUB_RELEASES_URL,
    REQUIRED_SUBMODULES,
    SKIPPED_SUBMODULES,
    check_git,
    configure_username,
    download_database,
    get_git_install_instructions,
    get_latest_db_release_url,
    get_submodules_to_init,
    init_submodules,
)


# ---------------------------------------------------------------------------
# Git detection
# ---------------------------------------------------------------------------


class TestCheckGit:
    """Test git detection logic across platforms."""

    @patch("scripts.onboarding.contributor_setup.subprocess.run")
    @patch("scripts.onboarding.contributor_setup.shutil.which")
    def test_git_found_and_working(
        self, mock_which: MagicMock, mock_run: MagicMock
    ) -> None:
        mock_which.return_value = "/usr/bin/git"
        mock_run.return_value = MagicMock(returncode=0, stdout="git version 2.43.0")

        available, version = check_git()

        assert available is True
        assert "2.43.0" in version

    @patch("scripts.onboarding.contributor_setup.shutil.which")
    def test_git_not_found(self, mock_which: MagicMock) -> None:
        mock_which.return_value = None

        available, message = check_git()

        assert available is False
        assert message  # should contain install instructions

    @patch("scripts.onboarding.contributor_setup.subprocess.run")
    @patch("scripts.onboarding.contributor_setup.shutil.which")
    def test_git_found_but_broken(
        self, mock_which: MagicMock, mock_run: MagicMock
    ) -> None:
        mock_which.return_value = "/usr/bin/git"
        mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="error")

        available, _ = check_git()

        assert available is False

    @patch("scripts.onboarding.contributor_setup.subprocess.run")
    @patch("scripts.onboarding.contributor_setup.shutil.which")
    def test_git_timeout(self, mock_which: MagicMock, mock_run: MagicMock) -> None:
        """Handles macOS Xcode shim that hangs."""
        import subprocess

        mock_which.return_value = "/usr/bin/git"
        mock_run.side_effect = subprocess.TimeoutExpired(cmd="git", timeout=10)

        available, _ = check_git()

        assert available is False


class TestGitInstallInstructions:
    """Test OS-specific install instructions."""

    @patch("scripts.onboarding.contributor_setup.platform.system")
    def test_linux_instructions(self, mock_system: MagicMock) -> None:
        mock_system.return_value = "Linux"
        instructions = get_git_install_instructions()
        assert "apt" in instructions or "dnf" in instructions

    @patch("scripts.onboarding.contributor_setup.platform.system")
    def test_macos_instructions(self, mock_system: MagicMock) -> None:
        mock_system.return_value = "Darwin"
        instructions = get_git_install_instructions()
        assert "xcode" in instructions.lower() or "brew" in instructions.lower()

    @patch("scripts.onboarding.contributor_setup.platform.system")
    def test_windows_instructions(self, mock_system: MagicMock) -> None:
        mock_system.return_value = "Windows"
        instructions = get_git_install_instructions()
        assert "git-scm.com" in instructions or "winget" in instructions


# ---------------------------------------------------------------------------
# Selective submodule initialization
# ---------------------------------------------------------------------------


class TestSubmoduleSelection:
    """Test which submodules are selected for initialization."""

    def test_required_submodules_include_sc_data(self) -> None:
        assert "resources/sc-data" in REQUIRED_SUBMODULES

    def test_required_submodules_include_dpd_submodules(self) -> None:
        assert "resources/dpd_submodules" in REQUIRED_SUBMODULES

    def test_skipped_submodules_exclude_export_only(self) -> None:
        export_only = {
            "resources/dpd_audio",
            "resources/other-dictionaries",
            "resources/tpr_downloads",
            "resources/bw2",
            "resources/fdg_dpd",
            "resources/tipitaka_translation_db",
        }
        for submodule in export_only:
            assert submodule in SKIPPED_SUBMODULES

    def test_get_submodules_to_init_returns_only_required(self) -> None:
        result = get_submodules_to_init()
        for submodule in result:
            assert submodule not in SKIPPED_SUBMODULES
        for required in REQUIRED_SUBMODULES:
            assert required in result


class TestInitSubmodules:
    """Test submodule initialization via git commands."""

    @patch("scripts.onboarding.contributor_setup.subprocess.run")
    def test_init_submodules_calls_git_for_each_required(
        self, mock_run: MagicMock, tmp_path: Path
    ) -> None:
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

        init_submodules(tmp_path)

        git_calls = [
            call for call in mock_run.call_args_list if "submodule" in str(call)
        ]
        assert len(git_calls) >= len(REQUIRED_SUBMODULES)

    @patch("scripts.onboarding.contributor_setup.subprocess.run")
    def test_init_submodules_never_inits_skipped(
        self, mock_run: MagicMock, tmp_path: Path
    ) -> None:
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

        init_submodules(tmp_path)

        all_call_args = str(mock_run.call_args_list)
        for skipped in SKIPPED_SUBMODULES:
            assert skipped not in all_call_args


# ---------------------------------------------------------------------------
# Database download from GitHub Releases
# ---------------------------------------------------------------------------


class TestGetLatestDbReleaseUrl:
    """Test fetching the latest release URL from GitHub API."""

    @patch("scripts.onboarding.contributor_setup.requests.get")
    def test_returns_download_url_for_dpd_db(self, mock_get: MagicMock) -> None:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "assets": [
                {
                    "name": "dpd.db.tar.gz",
                    "browser_download_url": "https://github.com/digitalpalidictionary/dpd-db/releases/download/v1.0/dpd.db.tar.gz",
                },
                {
                    "name": "dpd-goldendict.zip",
                    "browser_download_url": "https://example.com/other.zip",
                },
            ]
        }
        mock_get.return_value = mock_response

        url = get_latest_db_release_url()

        assert url is not None
        assert "dpd.db" in url

    @patch("scripts.onboarding.contributor_setup.requests.get")
    def test_returns_none_on_network_error(self, mock_get: MagicMock) -> None:
        import requests

        mock_get.side_effect = requests.exceptions.ConnectionError("no internet")

        url = get_latest_db_release_url()

        assert url is None

    @patch("scripts.onboarding.contributor_setup.requests.get")
    def test_returns_none_when_no_db_asset(self, mock_get: MagicMock) -> None:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "assets": [
                {
                    "name": "dpd-goldendict.zip",
                    "browser_download_url": "https://example.com/other.zip",
                }
            ]
        }
        mock_get.return_value = mock_response

        url = get_latest_db_release_url()

        assert url is None


class TestDownloadDatabase:
    """Test database file download."""

    @patch("scripts.onboarding.contributor_setup.requests.get")
    def test_downloads_to_correct_path(
        self, mock_get: MagicMock, tmp_path: Path
    ) -> None:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {"content-length": "100"}
        mock_response.iter_content.return_value = [b"fake_db_content"]
        mock_response.__enter__ = lambda s: s
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_get.return_value = mock_response

        dest = tmp_path / "dpd.db"
        result = download_database("https://example.com/dpd.db", dest)

        assert result is True
        assert dest.exists()
        assert dest.read_bytes() == b"fake_db_content"

    @patch("scripts.onboarding.contributor_setup.requests.get")
    def test_returns_false_on_network_error(
        self, mock_get: MagicMock, tmp_path: Path
    ) -> None:
        import requests

        mock_get.side_effect = requests.exceptions.ConnectionError("no internet")

        dest = tmp_path / "dpd.db"
        result = download_database("https://example.com/dpd.db", dest)

        assert result is False
        assert not dest.exists()


# ---------------------------------------------------------------------------
# Contributor username configuration
# ---------------------------------------------------------------------------


class TestConfigureUsername:
    """Test contributor username storage."""

    @patch("scripts.onboarding.contributor_setup.config_update")
    def test_stores_username_in_config(self, mock_update: MagicMock) -> None:
        configure_username("testuser")

        mock_update.assert_called_once_with("gui2", "username", "testuser", silent=True)

    @patch("scripts.onboarding.contributor_setup.config_update")
    def test_strips_whitespace_from_username(self, mock_update: MagicMock) -> None:
        configure_username("  testuser  ")

        mock_update.assert_called_once_with("gui2", "username", "testuser", silent=True)

    def test_rejects_empty_username(self) -> None:
        with pytest.raises(ValueError, match="[Uu]sername"):
            configure_username("")

    def test_rejects_whitespace_only_username(self) -> None:
        with pytest.raises(ValueError, match="[Uu]sername"):
            configure_username("   ")


# ---------------------------------------------------------------------------
# Idempotent re-runs
# ---------------------------------------------------------------------------


class TestIdempotentRerun:
    """Test that running setup multiple times is safe."""

    @patch("scripts.onboarding.contributor_setup.config_update")
    def test_configure_username_overwrites_existing(
        self, mock_update: MagicMock
    ) -> None:
        configure_username("newuser")

        mock_update.assert_called_once_with("gui2", "username", "newuser", silent=True)

    @patch("scripts.onboarding.contributor_setup.requests.get")
    def test_download_database_overwrites_existing_file(
        self, mock_get: MagicMock, tmp_path: Path
    ) -> None:
        dest = tmp_path / "dpd.db"
        dest.write_bytes(b"old_content")

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {"content-length": "100"}
        mock_response.iter_content.return_value = [b"new_content"]
        mock_response.__enter__ = lambda s: s
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_get.return_value = mock_response

        result = download_database("https://example.com/dpd.db", dest)

        assert result is True
        assert dest.read_bytes() == b"new_content"

    @patch("scripts.onboarding.contributor_setup.subprocess.run")
    def test_init_submodules_safe_to_rerun(
        self, mock_run: MagicMock, tmp_path: Path
    ) -> None:
        """Re-running submodule init should not error."""
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

        init_submodules(tmp_path)
        init_submodules(tmp_path)

        assert mock_run.call_count >= len(REQUIRED_SUBMODULES) * 2


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------


class TestConstants:
    """Test that important constants are correctly defined."""

    def test_github_releases_url_points_to_dpd_db(self) -> None:
        assert "digitalpalidictionary/dpd-db" in GITHUB_RELEASES_URL
        assert "releases" in GITHUB_RELEASES_URL
