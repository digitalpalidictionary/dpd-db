"""Tests for data submission via git commit and push."""

from pathlib import Path
from unittest.mock import MagicMock, patch


from scripts.onboarding.data_submission import (
    CONTRIBUTOR_DATA_FILES,
    build_commit_message,
    find_changed_data_files,
    submit_data,
)


class TestContributorDataFiles:
    """Test that the data file list is correctly defined."""

    def test_includes_additions(self) -> None:
        assert any("additions" in f for f in CONTRIBUTOR_DATA_FILES)

    def test_includes_corrections(self) -> None:
        assert any("corrections" in f for f in CONTRIBUTOR_DATA_FILES)


class TestFindChangedDataFiles:
    """Test detection of modified contributor data files."""

    @patch("scripts.onboarding.data_submission.subprocess.run")
    def test_returns_changed_files(self, mock_run: MagicMock) -> None:
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout=" M shared_data/additions.tsv\n",
        )

        result = find_changed_data_files(Path("/fake/project"))

        assert len(result) >= 1
        assert any("additions" in f for f in result)

    @patch("scripts.onboarding.data_submission.subprocess.run")
    def test_returns_empty_when_no_changes(self, mock_run: MagicMock) -> None:
        mock_run.return_value = MagicMock(returncode=0, stdout="")

        result = find_changed_data_files(Path("/fake/project"))

        assert result == []

    @patch("scripts.onboarding.data_submission.subprocess.run")
    def test_filters_only_contributor_data_files(self, mock_run: MagicMock) -> None:
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout=(
                " M shared_data/additions.tsv\n"
                " M shared_data/corrections.tsv\n"
                " M some/other/file.py\n"
            ),
        )

        result = find_changed_data_files(Path("/fake/project"))

        assert all(
            any(contrib_file in f for contrib_file in CONTRIBUTOR_DATA_FILES)
            for f in result
        )


class TestBuildCommitMessage:
    """Test auto-generated commit message."""

    def test_includes_username(self) -> None:
        msg = build_commit_message("johndoe")
        assert "johndoe" in msg

    def test_includes_date(self) -> None:
        msg = build_commit_message("johndoe")
        # should contain a date-like pattern (YYYY-MM-DD)
        import re

        assert re.search(r"\d{4}-\d{2}-\d{2}", msg)

    def test_has_contrib_prefix(self) -> None:
        msg = build_commit_message("johndoe")
        assert msg.startswith("contrib")


class TestSubmitData:
    """Test the full submit workflow: add, commit, push."""

    @patch("scripts.onboarding.data_submission.config_read")
    @patch("scripts.onboarding.data_submission.subprocess.run")
    def test_stages_commits_and_pushes(
        self, mock_run: MagicMock, mock_config: MagicMock
    ) -> None:
        mock_config.return_value = "testuser"
        mock_run.return_value = MagicMock(
            returncode=0, stdout=" M shared_data/additions.tsv\n"
        )

        result = submit_data(Path("/fake/project"))

        assert result.success is True
        call_args_list = [str(c) for c in mock_run.call_args_list]
        assert any("add" in c for c in call_args_list)
        assert any("commit" in c for c in call_args_list)
        assert any("push" in c for c in call_args_list)

    @patch("scripts.onboarding.data_submission.config_read")
    @patch("scripts.onboarding.data_submission.subprocess.run")
    def test_returns_failure_when_no_changes(
        self, mock_run: MagicMock, mock_config: MagicMock
    ) -> None:
        mock_config.return_value = "testuser"
        mock_run.return_value = MagicMock(returncode=0, stdout="")

        result = submit_data(Path("/fake/project"))

        assert result.success is False
        assert "no changes" in result.message.lower()

    @patch("scripts.onboarding.data_submission.config_read")
    @patch("scripts.onboarding.data_submission.subprocess.run")
    def test_returns_failure_when_no_username(
        self, mock_run: MagicMock, mock_config: MagicMock
    ) -> None:
        mock_config.return_value = None

        result = submit_data(Path("/fake/project"))

        assert result.success is False
        assert "username" in result.message.lower()

    @patch("scripts.onboarding.data_submission.config_read")
    @patch("scripts.onboarding.data_submission.subprocess.run")
    def test_returns_failure_on_push_error(
        self, mock_run: MagicMock, mock_config: MagicMock
    ) -> None:
        mock_config.return_value = "testuser"

        def side_effect(cmd, **kwargs):
            if "push" in cmd:
                return MagicMock(returncode=1, stderr="push rejected")
            if "status" in cmd:
                return MagicMock(returncode=0, stdout=" M shared_data/additions.tsv\n")
            return MagicMock(returncode=0, stdout="")

        mock_run.side_effect = side_effect

        result = submit_data(Path("/fake/project"))

        assert result.success is False

    @patch("scripts.onboarding.data_submission.config_read")
    @patch("scripts.onboarding.data_submission.subprocess.run")
    def test_retries_with_pull_on_push_rejection(
        self, mock_run: MagicMock, mock_config: MagicMock
    ) -> None:
        mock_config.return_value = "testuser"

        call_count = 0

        def side_effect(cmd, **kwargs):
            nonlocal call_count
            if "push" in cmd:
                call_count += 1
                if call_count == 1:
                    return MagicMock(returncode=1, stderr="rejected")
                return MagicMock(returncode=0, stdout="")
            if "status" in cmd:
                return MagicMock(returncode=0, stdout=" M shared_data/additions.tsv\n")
            return MagicMock(returncode=0, stdout="")

        mock_run.side_effect = side_effect

        submit_data(Path("/fake/project"))

        call_strs = [str(c) for c in mock_run.call_args_list]
        assert any("pull" in c for c in call_strs)
