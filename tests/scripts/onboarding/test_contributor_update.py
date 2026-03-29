"""Tests for contributor update script."""

from pathlib import Path
from unittest.mock import MagicMock, patch

from scripts.onboarding.contributor_update import (
    check_db_update_available,
    pull_latest_code,
    sync_dependencies,
    update_environment,
)


class TestPullLatestCode:
    """Test git pull logic."""

    @patch("scripts.onboarding.contributor_update.subprocess.run")
    def test_successful_pull(self, mock_run: MagicMock) -> None:
        mock_run.return_value = MagicMock(returncode=0, stdout="Already up to date.\n")

        success, message = pull_latest_code(Path("/fake/project"))

        assert success is True
        args = mock_run.call_args[0][0]
        assert "pull" in args

    @patch("scripts.onboarding.contributor_update.subprocess.run")
    def test_pull_with_network_error(self, mock_run: MagicMock) -> None:
        mock_run.return_value = MagicMock(
            returncode=1, stderr="fatal: unable to access"
        )

        success, message = pull_latest_code(Path("/fake/project"))

        assert success is False
        assert message  # should contain error info

    @patch("scripts.onboarding.contributor_update.subprocess.run")
    def test_pull_with_dirty_worktree(self, mock_run: MagicMock) -> None:
        mock_run.return_value = MagicMock(
            returncode=1,
            stderr="error: cannot pull with rebase: You have unstaged changes",
        )

        success, message = pull_latest_code(Path("/fake/project"))

        assert success is False


class TestSyncDependencies:
    """Test uv sync."""

    @patch("scripts.onboarding.contributor_update.subprocess.run")
    def test_successful_sync(self, mock_run: MagicMock) -> None:
        mock_run.return_value = MagicMock(returncode=0)

        success = sync_dependencies(Path("/fake/project"))

        assert success is True

    @patch("scripts.onboarding.contributor_update.subprocess.run")
    def test_sync_failure(self, mock_run: MagicMock) -> None:
        mock_run.return_value = MagicMock(returncode=1, stderr="error")

        success = sync_dependencies(Path("/fake/project"))

        assert success is False


class TestCheckDbUpdateAvailable:
    """Test database version comparison against GitHub Releases."""

    @patch("scripts.onboarding.contributor_update.requests.get")
    def test_update_available_when_newer_version(self, mock_get: MagicMock) -> None:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "tag_name": "v2.0",
            "assets": [
                {
                    "name": "dpd.db.tar.gz",
                    "browser_download_url": "https://example.com/dpd.db.tar.gz",
                }
            ],
        }
        mock_get.return_value = mock_response

        available, url = check_db_update_available("v1.0")

        assert available is True
        assert url is not None

    @patch("scripts.onboarding.contributor_update.requests.get")
    def test_no_update_when_same_version(self, mock_get: MagicMock) -> None:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "tag_name": "v1.0",
            "assets": [],
        }
        mock_get.return_value = mock_response

        available, url = check_db_update_available("v1.0")

        assert available is False

    @patch("scripts.onboarding.contributor_update.requests.get")
    def test_returns_false_on_network_error(self, mock_get: MagicMock) -> None:
        import requests

        mock_get.side_effect = requests.exceptions.ConnectionError("no internet")

        available, url = check_db_update_available("v1.0")

        assert available is False
        assert url is None


class TestUpdateEnvironment:
    """Test the full update workflow."""

    @patch("scripts.onboarding.contributor_update.check_db_update_available")
    @patch("scripts.onboarding.contributor_update.subprocess.run")
    def test_runs_pull_and_sync(
        self, mock_run: MagicMock, mock_db_check: MagicMock
    ) -> None:
        mock_run.return_value = MagicMock(returncode=0, stdout="")
        mock_db_check.return_value = (False, None)

        update_environment(Path("/fake/project"))

        call_strs = [str(c) for c in mock_run.call_args_list]
        assert any("pull" in c for c in call_strs)
        assert any("sync" in c for c in call_strs)

    @patch("scripts.onboarding.contributor_update.check_db_update_available")
    @patch("scripts.onboarding.contributor_update.subprocess.run")
    def test_reports_summary(
        self, mock_run: MagicMock, mock_db_check: MagicMock
    ) -> None:
        mock_run.return_value = MagicMock(returncode=0, stdout="")
        mock_db_check.return_value = (False, None)

        result = update_environment(Path("/fake/project"))

        assert "pull" in result.lower() or "update" in result.lower()

    @patch("scripts.onboarding.contributor_update.backup_database")
    @patch("scripts.onboarding.contributor_setup.download_database")
    @patch("scripts.onboarding.contributor_update.check_db_update_available")
    @patch("scripts.onboarding.contributor_update.subprocess.run")
    def test_downloads_db_when_new_version_available(
        self,
        mock_run: MagicMock,
        mock_db_check: MagicMock,
        mock_download: MagicMock,
        mock_backup: MagicMock,
    ) -> None:
        mock_run.return_value = MagicMock(returncode=0, stdout="")
        mock_db_check.return_value = (True, "https://example.com/dpd.db")
        mock_backup.return_value = (True, "backup_path")
        mock_download.return_value = True

        result = update_environment(Path("/fake/project"))

        mock_download.assert_called_once()
        assert "updated" in result.lower()
