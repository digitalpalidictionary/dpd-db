"""Tests for desktop shortcut creation across platforms."""

import stat
from pathlib import Path
from unittest.mock import MagicMock, patch

from scripts.onboarding.desktop_shortcut import (
    create_desktop_shortcut,
    create_linux_shortcut,
    create_macos_shortcut,
    create_windows_shortcut,
)


class TestLinuxShortcut:
    """Test .desktop file creation for Linux."""

    def test_creates_desktop_file(self, tmp_path: Path) -> None:
        project_root = tmp_path / "project"
        project_root.mkdir()
        desktop_dir = tmp_path / "Desktop"
        desktop_dir.mkdir()

        result = create_linux_shortcut(project_root, desktop_dir)

        assert result.exists()
        assert result.suffix == ".desktop"

    def test_desktop_file_contains_required_fields(self, tmp_path: Path) -> None:
        project_root = tmp_path / "project"
        project_root.mkdir()
        desktop_dir = tmp_path / "Desktop"
        desktop_dir.mkdir()

        result = create_linux_shortcut(project_root, desktop_dir)
        content = result.read_text()

        assert "[Desktop Entry]" in content
        assert "Type=Application" in content
        assert "Name=" in content
        assert "Exec=" in content
        assert f"Path={project_root}" in content

    def test_desktop_file_uses_terminal(self, tmp_path: Path) -> None:
        project_root = tmp_path / "project"
        project_root.mkdir()
        desktop_dir = tmp_path / "Desktop"
        desktop_dir.mkdir()

        result = create_linux_shortcut(project_root, desktop_dir)
        content = result.read_text()

        assert "Terminal=true" in content

    def test_desktop_file_is_executable(self, tmp_path: Path) -> None:
        project_root = tmp_path / "project"
        project_root.mkdir()
        desktop_dir = tmp_path / "Desktop"
        desktop_dir.mkdir()

        result = create_linux_shortcut(project_root, desktop_dir)

        assert result.stat().st_mode & stat.S_IEXEC


class TestMacosShortcut:
    """Test .command file creation for macOS."""

    def test_creates_command_file(self, tmp_path: Path) -> None:
        project_root = tmp_path / "project"
        project_root.mkdir()
        desktop_dir = tmp_path / "Desktop"
        desktop_dir.mkdir()

        result = create_macos_shortcut(project_root, desktop_dir)

        assert result.exists()
        assert result.suffix == ".command"

    def test_command_file_sets_working_directory(self, tmp_path: Path) -> None:
        project_root = tmp_path / "project"
        project_root.mkdir()
        desktop_dir = tmp_path / "Desktop"
        desktop_dir.mkdir()

        result = create_macos_shortcut(project_root, desktop_dir)
        content = result.read_text()

        assert f'cd "{project_root}"' in content

    def test_command_file_launches_gui(self, tmp_path: Path) -> None:
        project_root = tmp_path / "project"
        project_root.mkdir()
        desktop_dir = tmp_path / "Desktop"
        desktop_dir.mkdir()

        result = create_macos_shortcut(project_root, desktop_dir)
        content = result.read_text()

        assert "uv run scripts/onboarding/launch_gui.py" in content

    def test_command_file_is_executable(self, tmp_path: Path) -> None:
        project_root = tmp_path / "project"
        project_root.mkdir()
        desktop_dir = tmp_path / "Desktop"
        desktop_dir.mkdir()

        result = create_macos_shortcut(project_root, desktop_dir)

        assert result.stat().st_mode & stat.S_IEXEC

    def test_command_file_has_shebang(self, tmp_path: Path) -> None:
        project_root = tmp_path / "project"
        project_root.mkdir()
        desktop_dir = tmp_path / "Desktop"
        desktop_dir.mkdir()

        result = create_macos_shortcut(project_root, desktop_dir)
        content = result.read_text()

        assert content.startswith("#!/")


class TestWindowsShortcut:
    """Test .bat file creation for Windows."""

    def test_creates_bat_file(self, tmp_path: Path) -> None:
        project_root = tmp_path / "project"
        project_root.mkdir()
        desktop_dir = tmp_path / "Desktop"
        desktop_dir.mkdir()

        result = create_windows_shortcut(project_root, desktop_dir)

        assert result.exists()
        assert result.suffix == ".bat"

    def test_bat_file_sets_working_directory(self, tmp_path: Path) -> None:
        project_root = tmp_path / "project"
        project_root.mkdir()
        desktop_dir = tmp_path / "Desktop"
        desktop_dir.mkdir()

        result = create_windows_shortcut(project_root, desktop_dir)
        content = result.read_text()

        assert f'cd /d "{project_root}"' in content

    def test_bat_file_launches_gui(self, tmp_path: Path) -> None:
        project_root = tmp_path / "project"
        project_root.mkdir()
        desktop_dir = tmp_path / "Desktop"
        desktop_dir.mkdir()

        result = create_windows_shortcut(project_root, desktop_dir)
        content = result.read_text()

        assert "uv run scripts/onboarding/launch_gui.py" in content


class TestCreateDesktopShortcut:
    """Test the platform dispatcher."""

    @patch("scripts.onboarding.desktop_shortcut.platform.system")
    def test_dispatches_to_linux(self, mock_system: MagicMock, tmp_path: Path) -> None:
        mock_system.return_value = "Linux"
        project_root = tmp_path / "project"
        project_root.mkdir()
        desktop_dir = tmp_path / "Desktop"
        desktop_dir.mkdir()

        result = create_desktop_shortcut(project_root, desktop_dir)

        assert result.suffix == ".desktop"

    @patch("scripts.onboarding.desktop_shortcut.platform.system")
    def test_dispatches_to_macos(self, mock_system: MagicMock, tmp_path: Path) -> None:
        mock_system.return_value = "Darwin"
        project_root = tmp_path / "project"
        project_root.mkdir()
        desktop_dir = tmp_path / "Desktop"
        desktop_dir.mkdir()

        result = create_desktop_shortcut(project_root, desktop_dir)

        assert result.suffix == ".command"

    @patch("scripts.onboarding.desktop_shortcut.platform.system")
    def test_dispatches_to_windows(
        self, mock_system: MagicMock, tmp_path: Path
    ) -> None:
        mock_system.return_value = "Windows"
        project_root = tmp_path / "project"
        project_root.mkdir()
        desktop_dir = tmp_path / "Desktop"
        desktop_dir.mkdir()

        result = create_desktop_shortcut(project_root, desktop_dir)

        assert result.suffix == ".bat"

    @patch("scripts.onboarding.desktop_shortcut.platform.system")
    def test_raises_on_unsupported_platform(
        self, mock_system: MagicMock, tmp_path: Path
    ) -> None:
        mock_system.return_value = "FreeBSD"
        project_root = tmp_path / "project"
        project_root.mkdir()
        desktop_dir = tmp_path / "Desktop"
        desktop_dir.mkdir()

        import pytest

        with pytest.raises(OSError, match="Unsupported"):
            create_desktop_shortcut(project_root, desktop_dir)

    def test_idempotent_overwrites_existing(self, tmp_path: Path) -> None:
        """Creating shortcut twice should overwrite without error."""
        project_root = tmp_path / "project"
        project_root.mkdir()
        desktop_dir = tmp_path / "Desktop"
        desktop_dir.mkdir()

        result1 = create_linux_shortcut(project_root, desktop_dir)
        result2 = create_linux_shortcut(project_root, desktop_dir)

        assert result1 == result2
        assert result2.exists()
