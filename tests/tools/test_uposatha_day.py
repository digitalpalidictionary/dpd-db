"""Tests for tools/uposatha_day.py uposatha-day detection and count rotation.

UposathaManger caches its parsed config as a class attribute (`_config`), so
every test resets that cache and patches ProjectPaths to point at a tmp_path
ini instead of the real tools/uposatha_day.ini. `date.today()` is frozen via
a date subclass so assertions never depend on the day the test happens to run.
"""

import configparser
from datetime import date
from pathlib import Path

import pytest

from tools import uposatha_day as uposatha_day_module
from tools.uposatha_day import UposathaManger


class _StubPaths:
    def __init__(self, ini_path: Path) -> None:
        self.uposatha_day_ini = ini_path


@pytest.fixture(autouse=True)
def _reset_config_cache():
    if hasattr(UposathaManger, "_config"):
        del UposathaManger._config
    yield
    if hasattr(UposathaManger, "_config"):
        del UposathaManger._config


def _freeze_today(monkeypatch: pytest.MonkeyPatch, fixed: date) -> None:
    class _Frozen(date):
        @classmethod
        def today(cls) -> date:
            return fixed

    monkeypatch.setattr(uposatha_day_module, "date", _Frozen)


def _use_ini(monkeypatch: pytest.MonkeyPatch, tmp_path: Path, contents: str) -> Path:
    ini_path = tmp_path / "uposatha_day.ini"
    ini_path.write_text(contents, encoding="utf-8")
    monkeypatch.setattr(
        uposatha_day_module, "ProjectPaths", lambda: _StubPaths(ini_path)
    )
    return ini_path


def test_uposatha_today_true_on_listed_date(monkeypatch: pytest.MonkeyPatch) -> None:
    _freeze_today(monkeypatch, date(2026, 5, 1))
    assert UposathaManger.uposatha_today() is True


def test_uposatha_today_false_on_non_listed_date(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _freeze_today(monkeypatch, date(2026, 5, 2))
    assert UposathaManger.uposatha_today() is False


def test_day_after_uposatha_true(monkeypatch: pytest.MonkeyPatch) -> None:
    _freeze_today(monkeypatch, date(2026, 5, 2))
    assert UposathaManger.day_after_uposatha() is True


def test_day_after_uposatha_false(monkeypatch: pytest.MonkeyPatch) -> None:
    _freeze_today(monkeypatch, date(2026, 5, 1))
    assert UposathaManger.day_after_uposatha() is False


def test_get_baseline_count_returns_count_when_not_rotated_today(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    _freeze_today(monkeypatch, date(2026, 6, 1))
    _use_ini(
        monkeypatch,
        tmp_path,
        "[uposatha]\nprevious_count = 100\ncount = 200\ndate = 2026-05-01\n",
    )
    assert UposathaManger.get_baseline_count() == 200


def test_get_baseline_count_returns_previous_count_when_already_rotated_today(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    _freeze_today(monkeypatch, date(2026, 6, 1))
    _use_ini(
        monkeypatch,
        tmp_path,
        "[uposatha]\nprevious_count = 100\ncount = 200\ndate = 2026-06-01\n",
    )
    assert UposathaManger.get_baseline_count() == 100


def test_get_baseline_count_raises_when_ini_has_no_section(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Locks current (buggy) behaviour: get_baseline_count only catches
    NoOptionError/ValueError, not NoSectionError, so a section-less ini
    crashes instead of falling back to 0."""
    _freeze_today(monkeypatch, date(2026, 6, 1))
    _use_ini(monkeypatch, tmp_path, "")
    with pytest.raises(configparser.NoSectionError):
        UposathaManger.get_baseline_count()


def test_rotate_count_writes_new_values_and_rotates_previous(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    _freeze_today(monkeypatch, date(2026, 6, 1))
    ini_path = _use_ini(
        monkeypatch,
        tmp_path,
        "[uposatha]\nprevious_count = 100\ncount = 200\ndate = 2026-05-01\n",
    )

    assert UposathaManger.rotate_count(300) is True

    written = configparser.ConfigParser()
    written.read(ini_path)
    assert written.get("uposatha", "previous_count") == "200"
    assert written.get("uposatha", "count") == "300"
    assert written.get("uposatha", "date") == "2026-06-01"


def test_rotate_count_skips_if_already_rotated_today(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    _freeze_today(monkeypatch, date(2026, 6, 1))
    ini_path = _use_ini(
        monkeypatch,
        tmp_path,
        "[uposatha]\nprevious_count = 100\ncount = 200\ndate = 2026-06-01\n",
    )

    assert UposathaManger.rotate_count(999) is True

    written = configparser.ConfigParser()
    written.read(ini_path)
    assert written.get("uposatha", "count") == "200"
