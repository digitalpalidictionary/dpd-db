import json
import os
import stat
from datetime import UTC, datetime, timedelta, timezone
from pathlib import Path

import pytest

from tools.contrib_notice import (
    STALE_SECONDS,
    read_notice,
    remove_notice,
    write_notice,
)

NOW = datetime(2026, 11, 9, 19, 0, 0, tzinfo=UTC)


def test_round_trip(tmp_path: Path) -> None:
    path = tmp_path / "notice.json"
    stop = NOW + timedelta(minutes=30)
    write_notice(path, stop)
    assert read_notice(path, NOW) == (stop, "ok")


def test_naive_datetime_refused(tmp_path: Path) -> None:
    with pytest.raises(ValueError):
        write_notice(tmp_path / "n.json", datetime(2026, 11, 9, 19, 0))


def test_non_utc_datetime_refused(tmp_path: Path) -> None:
    local = datetime(
        2026, 11, 9, 19, 0, tzinfo=timezone(timedelta(hours=5, minutes=30))
    )
    with pytest.raises(ValueError):
        write_notice(tmp_path / "n.json", local)


def test_absent(tmp_path: Path) -> None:
    assert read_notice(tmp_path / "none.json", NOW) == (None, "absent")


def test_garbage_json(tmp_path: Path) -> None:
    path = tmp_path / "n.json"
    path.write_text("{not json")
    assert read_notice(path, NOW) == (None, "unreadable")


def test_json_list(tmp_path: Path) -> None:
    path = tmp_path / "n.json"
    path.write_text("[1, 2]")
    assert read_notice(path, NOW) == (None, "unreadable")


def test_directory_is_unreadable(tmp_path: Path) -> None:
    assert read_notice(tmp_path, NOW) == (None, "unreadable")


def test_missing_key(tmp_path: Path) -> None:
    path = tmp_path / "n.json"
    path.write_text(json.dumps({"other": 1}))
    assert read_notice(path, NOW) == (None, "bad time")


def test_time_not_a_string(tmp_path: Path) -> None:
    path = tmp_path / "n.json"
    path.write_text(json.dumps({"stop_at": 12345}))
    assert read_notice(path, NOW) == (None, "bad time")


def test_bad_time_string(tmp_path: Path) -> None:
    path = tmp_path / "n.json"
    path.write_text(json.dumps({"stop_at": "tomorrow"}))
    assert read_notice(path, NOW) == (None, "bad time")


def test_naive_time_string(tmp_path: Path) -> None:
    path = tmp_path / "n.json"
    path.write_text(json.dumps({"stop_at": "2026-11-09T19:30:00"}))
    assert read_notice(path, NOW) == (None, "bad time")


def test_past_by_61_seconds(tmp_path: Path) -> None:
    path = tmp_path / "n.json"
    write_notice(path, NOW - timedelta(seconds=STALE_SECONDS + 1))
    assert read_notice(path, NOW) == (None, "past")


def test_past_by_59_seconds_is_still_ok(tmp_path: Path) -> None:
    path = tmp_path / "n.json"
    stop = NOW - timedelta(seconds=STALE_SECONDS - 1)
    write_notice(path, stop)
    assert read_notice(path, NOW) == (stop, "ok")


def test_file_mode_is_644(tmp_path: Path) -> None:
    path = tmp_path / "n.json"
    write_notice(path, NOW)
    assert stat.S_IMODE(path.stat().st_mode) == 0o644


def test_file_mode_is_644_whatever_the_umask(tmp_path: Path) -> None:
    path = tmp_path / "n.json"
    old = os.umask(0o077)
    try:
        write_notice(path, NOW)
    finally:
        os.umask(old)
    assert stat.S_IMODE(path.stat().st_mode) == 0o644


def test_remove_returns_whether_a_file_was_there(tmp_path: Path) -> None:
    path = tmp_path / "n.json"
    write_notice(path, NOW)
    assert remove_notice(path) is True
    assert remove_notice(path) is False
