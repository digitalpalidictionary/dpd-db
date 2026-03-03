"""Tests for GUI launch wrapper."""

from unittest.mock import MagicMock, patch

from scripts.onboarding.launch_gui import launch_gui, sync_dependencies


class TestSyncDependencies:
    """Test uv sync dependency check."""

    @patch("scripts.onboarding.launch_gui.subprocess.run")
    def test_calls_uv_sync(self, mock_run: MagicMock) -> None:
        mock_run.return_value = MagicMock(returncode=0)

        result = sync_dependencies()

        assert result is True
        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        assert "uv" in args
        assert "sync" in args

    @patch("scripts.onboarding.launch_gui.subprocess.run")
    def test_returns_false_on_failure(self, mock_run: MagicMock) -> None:
        mock_run.return_value = MagicMock(returncode=1, stderr="error")

        result = sync_dependencies()

        assert result is False

    @patch("scripts.onboarding.launch_gui.subprocess.run")
    def test_returns_false_on_missing_uv(self, mock_run: MagicMock) -> None:
        mock_run.side_effect = FileNotFoundError("uv not found")

        result = sync_dependencies()

        assert result is False


class TestLaunchGui:
    """Test GUI launch invocation."""

    @patch("scripts.onboarding.launch_gui.subprocess.run")
    def test_launches_gui2_main(self, mock_run: MagicMock) -> None:
        mock_run.return_value = MagicMock(returncode=0)

        launch_gui()

        calls = mock_run.call_args_list
        gui_call = calls[-1]
        args = gui_call[0][0]
        assert "gui2/main.py" in " ".join(str(a) for a in args)

    @patch("scripts.onboarding.launch_gui.subprocess.run")
    def test_syncs_before_launching(self, mock_run: MagicMock) -> None:
        mock_run.return_value = MagicMock(returncode=0)

        launch_gui()

        assert mock_run.call_count == 2
        first_call_args = mock_run.call_args_list[0][0][0]
        assert "sync" in first_call_args
