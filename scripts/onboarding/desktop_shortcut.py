"""Cross-platform desktop shortcut creation for DPD GUI.

Creates a clickable shortcut on the user's Desktop that launches the
GUI via `uv run scripts/onboarding/launch_gui.py`.
"""

import platform
import stat
import subprocess
from pathlib import Path


def create_linux_shortcut(project_root: Path, desktop_dir: Path | None = None) -> Path:
    """Create a .desktop file on the user's Desktop."""
    if desktop_dir is None:
        desktop_dir = Path.home() / "Desktop"

    desktop_file = desktop_dir / "dpd-gui.desktop"
    content = (
        "[Desktop Entry]\n"
        "Type=Application\n"
        "Name=DPD GUI\n"
        "Comment=Launch Digital Pali Dictionary GUI\n"
        f"Exec=uv run scripts/onboarding/launch_gui.py\n"
        f"Path={project_root}\n"
        "Terminal=true\n"
        "Icon=utilities-terminal\n"
        "Categories=Education;\n"
    )
    desktop_file.write_text(content)

    desktop_file.chmod(
        desktop_file.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH
    )

    try:
        subprocess.run(
            ["gio", "set", str(desktop_file), "metadata::trusted", "true"],
            check=False,
            capture_output=True,
        )
    except FileNotFoundError:
        pass

    return desktop_file


def create_macos_shortcut(project_root: Path, desktop_dir: Path | None = None) -> Path:
    """Create a .command file on the user's Desktop."""
    if desktop_dir is None:
        desktop_dir = Path.home() / "Desktop"

    command_file = desktop_dir / "DPD GUI.command"
    content = (
        f'#!/bin/zsh\ncd "{project_root}"\nuv run scripts/onboarding/launch_gui.py\n'
    )
    command_file.write_text(content)

    command_file.chmod(
        command_file.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH
    )

    return command_file


def create_windows_shortcut(
    project_root: Path, desktop_dir: Path | None = None
) -> Path:
    """Create a .bat file on the user's Desktop."""
    if desktop_dir is None:
        desktop_dir = Path.home() / "Desktop"

    bat_file = desktop_dir / "DPD GUI.bat"
    content = (
        "@echo off\n"
        f'cd /d "{project_root}"\n'
        "uv run scripts/onboarding/launch_gui.py\n"
        "pause\n"
    )
    bat_file.write_text(content)

    return bat_file


def create_desktop_shortcut(
    project_root: Path, desktop_dir: Path | None = None
) -> Path:
    """Create a platform-appropriate desktop shortcut."""
    system = platform.system()
    if system == "Linux":
        return create_linux_shortcut(project_root, desktop_dir)
    elif system == "Darwin":
        return create_macos_shortcut(project_root, desktop_dir)
    elif system == "Windows":
        return create_windows_shortcut(project_root, desktop_dir)
    else:
        raise OSError(f"Unsupported platform: {system}")
