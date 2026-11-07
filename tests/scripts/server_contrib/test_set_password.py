"""set_password.sh run for real under a temporary --root."""

import os
import shutil
import subprocess
from pathlib import Path

import pytest

SCRIPT = Path("scripts/server_contrib/set_password.sh")
ADD_SCRIPT = Path("scripts/server_contrib/add_contributor.sh")

pytestmark = pytest.mark.skipif(
    shutil.which("htpasswd") is None, reason="htpasswd (apache2-utils) not installed"
)


def add(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["bash", str(ADD_SCRIPT), "--root", str(root), *args],
        input="oldpass123\n",
        capture_output=True,
        text=True,
    )


def set_pw(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["bash", str(SCRIPT), "--root", str(root), *args],
        input="freshpass99\n",
        capture_output=True,
        text=True,
    )


def verify(root: Path, user: str, password: str) -> int:
    htpasswd_file = root / "etc" / "nginx" / "dpd" / f"{user}.htpasswd"
    return subprocess.run(
        ["htpasswd", "-v", "-i", str(htpasswd_file), user],
        input=f"{password}\n",
        capture_output=True,
        text=True,
    ).returncode


def test_reset_changes_the_hash_and_arms_the_marker(tmp_path: Path) -> None:
    assert add(tmp_path, "alice", "8551").returncode == 0
    assert verify(tmp_path, "alice", "oldpass123") == 0

    result = set_pw(tmp_path, "alice")
    assert result.returncode == 0

    assert verify(tmp_path, "alice", "oldpass123") == 3
    assert verify(tmp_path, "alice", "freshpass99") == 0

    marker = tmp_path / "etc" / "nginx" / "dpd" / "alice.initial"
    assert marker.is_file()
    assert (marker.stat().st_mode & 0o777) == 0o600


def test_mode_is_restored_to_640(tmp_path: Path) -> None:
    assert add(tmp_path, "bob", "8552").returncode == 0
    htpasswd_file = tmp_path / "etc" / "nginx" / "dpd" / "bob.htpasswd"
    os.chmod(htpasswd_file, 0o640)
    assert set_pw(tmp_path, "bob").returncode == 0
    assert (htpasswd_file.stat().st_mode & 0o777) == 0o640


def test_refuses_an_unknown_user(tmp_path: Path) -> None:
    result = set_pw(tmp_path, "nobody")
    assert result.returncode != 0
    assert "does not exist" in result.stderr


def test_hash_format_parity_with_add_contributor(tmp_path: Path) -> None:
    """Both scripts must emit the same bcrypt format ($2y$05$). A drift in
    cost or flags would make resets write hashes nginx treats differently —
    the manual_corrections.tsv two-readers lesson."""
    assert add(tmp_path, "carol", "8553").returncode == 0
    assert set_pw(tmp_path, "carol").returncode == 0

    htpasswd_file = tmp_path / "etc" / "nginx" / "dpd" / "carol.htpasswd"
    lines = htpasswd_file.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 1
    user, hash_ = lines[0].split(":", 1)
    assert user == "carol"
    assert hash_.startswith("$2y$05$"), hash_
