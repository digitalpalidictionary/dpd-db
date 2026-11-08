"""password_change.py core logic, with the real htpasswd binary."""

import base64
import os
import shutil
import subprocess
from pathlib import Path

import pytest

from scripts.server_contrib import password_change as pc
from scripts.server_contrib import password_service

pytestmark = pytest.mark.skipif(
    shutil.which("htpasswd") is None, reason="htpasswd (apache2-utils) not installed"
)


def run_htpasswd(args: list[str], input: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["htpasswd", *args], input=input, capture_output=True, text=True
    )


def make_store(
    tmp_path: Path, user: str = "alice", password: str = "oldpass123"
) -> pc.PasswordStore:
    result = run_htpasswd(
        ["-B", "-C", "5", "-i", "-c", str(tmp_path / f"{user}.htpasswd"), user],
        input=f"{password}\n",
    )
    assert result.returncode == 0
    return pc.PasswordStore(tmp_path)


def auth_header(user: str, password: str) -> str:
    return "Basic " + base64.b64encode(f"{user}:{password}".encode()).decode()


def verify(path: Path, user: str, password: str) -> int:
    return run_htpasswd(["-v", "-i", str(path), user], input=f"{password}\n").returncode


# -- write path --------------------------------------------------------------


def test_change_updates_hash(tmp_path: Path) -> None:
    store = make_store(tmp_path)
    store.change_password("alice", "brandnewpass1")
    htpasswd_file = tmp_path / "alice.htpasswd"
    assert verify(htpasswd_file, "alice", "oldpass123") == 3
    assert verify(htpasswd_file, "alice", "brandnewpass1") == 0


def test_mode_preserved(tmp_path: Path) -> None:
    store = make_store(tmp_path)
    htpasswd_file = tmp_path / "alice.htpasswd"
    os.chmod(htpasswd_file, 0o640)
    store.change_password("alice", "brandnewpass1")
    assert (htpasswd_file.stat().st_mode & 0o777) == 0o640


def test_gid_preserved_same_user(tmp_path: Path) -> None:
    store = make_store(tmp_path)
    htpasswd_file = tmp_path / "alice.htpasswd"
    gid_before = htpasswd_file.stat().st_gid
    store.change_password("alice", "brandnewpass1")
    assert htpasswd_file.stat().st_gid == gid_before


def test_bak_written_and_restore_on_replace_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    store = make_store(tmp_path)
    htpasswd_file = tmp_path / "alice.htpasswd"

    def broken_replace(src: Path, dst: Path) -> None:
        raise OSError("induced failure")

    monkeypatch.setattr(pc, "_replace", broken_replace)
    with pytest.raises(pc.ChangeError):
        store.change_password("alice", "brandnewpass1")
    assert verify(htpasswd_file, "alice", "oldpass123") == 0
    assert (tmp_path / "alice.htpasswd.bak").is_file()


def test_post_check_failure_restores(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A replace that lands with the wrong group is rolled back from .bak."""
    store = make_store(tmp_path)
    htpasswd_file = tmp_path / "alice.htpasswd"
    mode_before = htpasswd_file.stat().st_mode & 0o777

    real_apply_owner = pc._apply_owner

    def wrong_owner(path: Path, original: os.stat_result) -> None:
        real_apply_owner(path, original)
        os.chmod(path, 0o600)  # simulate a landed file with the wrong mode

    monkeypatch.setattr(pc, "_apply_owner", wrong_owner)
    with pytest.raises(pc.ChangeError) as excinfo:
        store.change_password("alice", "brandnewpass1")
    assert excinfo.value.reason == "post_check_failed"
    assert verify(htpasswd_file, "alice", "oldpass123") == 0
    assert (htpasswd_file.stat().st_mode & 0o777) == mode_before


def test_wrong_verify_never_replaces_nor_clears_marker(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    store = make_store(tmp_path)
    store.marker("alice").touch()
    htpasswd_file = tmp_path / "alice.htpasswd"
    real_run = pc._run_htpasswd

    def fail_verify(args: list[str], input: str) -> subprocess.CompletedProcess[str]:
        if "-v" in args:
            return subprocess.CompletedProcess(args, 3, "", "verification failed")
        return real_run(args, input)

    monkeypatch.setattr(pc, "_run_htpasswd", fail_verify)
    with pytest.raises(pc.ChangeError) as excinfo:
        store.change_password("alice", "brandnewpass1")
    assert excinfo.value.reason == "verify_failed"
    assert verify(htpasswd_file, "alice", "oldpass123") == 0
    assert store.needs_change("alice")
    assert not (tmp_path / ".alice.htpasswd.tmp").exists()


def test_marker_cleared_on_success(tmp_path: Path) -> None:
    store = make_store(tmp_path)
    store.marker("alice").touch()
    assert store.needs_change("alice")
    store.change_password("alice", "brandnewpass1")
    assert not store.needs_change("alice")


def test_length_bounds(tmp_path: Path) -> None:
    store = make_store(tmp_path)
    with pytest.raises(pc.ChangeError) as excinfo:
        store.change_password("alice", "ninechars")
    assert excinfo.value.reason == "too_short"
    store.change_password("alice", "tenchars12")
    store.change_password("alice", "a" * 72)
    with pytest.raises(pc.ChangeError) as excinfo:
        store.change_password("alice", "a" * 73)
    assert excinfo.value.reason == "too_long"


def test_unknown_user_rejected(tmp_path: Path) -> None:
    store = make_store(tmp_path)
    with pytest.raises(pc.ChangeError) as excinfo:
        store.change_password("bob", "brandnewpass1")
    assert excinfo.value.reason == "unknown_user"


# -- username rule -----------------------------------------------------------


@pytest.mark.parametrize(
    "user,expected",
    [
        ("alice", True),
        ("a", True),
        ("user_2", True),
        ("Alice", False),
        ("1abc", False),
        ("a" * 33, False),
        ("has-added-in", False),
        ("", False),
        ("../etc", False),
        ("alice\n", False),
    ],
)
def test_valid_username(user: str, expected: bool) -> None:
    assert pc.valid_username(user) is expected


# -- identity ----------------------------------------------------------------


def test_identify_user_matrix(tmp_path: Path) -> None:
    store = make_store(tmp_path)
    assert store.identify_user(None) is None
    assert store.identify_user("Bearer abc") is None
    assert store.identify_user("Basic !!!not-base64!!!") is None
    assert store.identify_user(auth_header("nobody", "pw")) is None
    assert store.identify_user(auth_header("alice", "oldpass123")) == "alice"


def test_check_gated_matrix(tmp_path: Path) -> None:
    store = make_store(tmp_path)
    store.marker("alice").touch()
    assert store.check_gated("alice") is True  # known user, marker armed
    assert store.check_gated("bob") is False  # unknown user
    store.clear_marker("alice")
    assert store.check_gated("alice") is False  # known user, no marker
    assert store.check_gated("../etc") is False  # invalid name


# -- CSRF decision -----------------------------------------------------------


def test_origin_allowed_matrix() -> None:
    assert pc.origin_allowed("https://dpd.example", None, "dpd.example") is True
    assert (
        pc.origin_allowed(None, "https://dpd.example/password/", "dpd.example") is True
    )
    assert pc.origin_allowed("https://evil.example", None, "dpd.example") is False
    assert pc.origin_allowed("https://dpd.example.evil", None, "dpd.example") is False
    assert pc.origin_allowed(None, None, "dpd.example") is False
    assert pc.origin_allowed(None, "https://dpd.example.evil/", "dpd.example") is False
    assert pc.origin_allowed("https://dpd.example", None, None) is False


def test_control_characters_are_rejected(tmp_path: Path) -> None:
    """htpasswd -i reads only the first line, so a line break in a hand-made
    POST would store a shorter password than the one sent."""
    store = make_store(tmp_path)
    store.marker("alice").touch()
    htpasswd_file = tmp_path / "alice.htpasswd"
    before = htpasswd_file.read_bytes()

    with pytest.raises(pc.ChangeError) as excinfo:
        store.change_password("alice", "abcdefghij\nklm")
    assert excinfo.value.reason == "bad_characters"

    assert htpasswd_file.read_bytes() == before
    assert store.needs_change("alice")


def test_service_store_is_one_shared_instance(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("DPD_HTPASSWD_DIR", str(tmp_path))
    password_service.store.cache_clear()
    try:
        assert password_service.store() is password_service.store()
    finally:
        password_service.store.cache_clear()


def test_form_page_has_show_passwords_box() -> None:
    page = password_service.form_page("alice")
    assert 'id="show"' in page
    assert "Show passwords" in page
    # The script is an f-string body: a lone brace would have raised, and the
    # doubled braces must come out as single ones.
    assert "box.type = kind;" in page
    assert "{{" not in page
