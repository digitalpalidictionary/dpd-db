"""add_contributor.sh run for real under a temporary --root."""

import shutil
import subprocess
from pathlib import Path

import pytest

from tools.contrib_entry import delivered_files

SCRIPT = Path("scripts/server_contrib/add_contributor.sh")

pytestmark = pytest.mark.skipif(
    shutil.which("htpasswd") is None, reason="htpasswd (apache2-utils) not installed"
)


def add(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["bash", str(SCRIPT), "--root", str(root), *args],
        input="secret\n",
        capture_output=True,
        text=True,
    )


def env_lines(root: Path, user: str) -> dict[str, str]:
    text = (root / "etc" / "dpd" / f"{user}.env").read_text(encoding="utf-8")
    return dict(line.split("=", 1) for line in text.splitlines())


def test_every_user_shares_one_flat_data_folder_the_sync_scripts_can_read(
    tmp_path: Path,
) -> None:
    assert add(tmp_path, "alice", "8551", "Bold Search,DB,√").returncode == 0
    assert add(tmp_path, "bob", "8552").returncode == 0

    alice, bob = env_lines(tmp_path, "alice"), env_lines(tmp_path, "bob")
    assert alice["DPD_GUI2_DATA_DIR"] == bob["DPD_GUI2_DATA_DIR"]
    assert alice["DPD_GUI2_TABS"] == '"Bold Search,DB,√"'

    # What the window globs is what the instances write: one folder, user in the
    # file name.
    data = tmp_path / alice["DPD_GUI2_DATA_DIR"].lstrip("/")
    assert data.is_dir()
    (data / "additions_alice.json").write_text("{}")
    (data / "additions_bob.json").write_text("{}")
    found = [p.name for p in delivered_files(data)["additions"]]
    assert found == ["additions_alice.json", "additions_bob.json"]


@pytest.mark.parametrize(
    ("args", "reason"),
    [
        (("1", "8555"), "starting with a letter"),
        (("x_added", "8555"), "added"),
        (("carol", "80"), "port"),
        (("carol", "8555", 'DB"\nINJECT=1'), "tabs"),
    ],
)
def test_bad_input_is_refused_and_creates_nothing(
    tmp_path: Path, args: tuple[str, ...], reason: str
) -> None:
    result = add(tmp_path, *args)

    assert result.returncode == 1
    assert reason in result.stderr
    assert list(tmp_path.rglob("*")) == []


def test_a_repeated_user_or_port_is_refused(tmp_path: Path) -> None:
    assert add(tmp_path, "alice", "8551").returncode == 0

    assert "already exists" in add(tmp_path, "alice", "8552").stderr
    assert "already used" in add(tmp_path, "bob", "8551").stderr
    assert not (tmp_path / "etc" / "dpd" / "bob.env").exists()


def test_each_user_gets_their_own_login_realm(tmp_path: Path) -> None:
    add(tmp_path, "alice", "8551")

    conf = (tmp_path / "etc" / "nginx" / "dpd" / "alice.conf").read_text()
    assert 'auth_basic "DPD contributor alice";' in conf
