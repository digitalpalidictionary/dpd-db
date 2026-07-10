from pathlib import Path

from gui2.daily_log import DailyLog
from gui2.paths import Gui2Paths
from gui2.toolkit import ToolKit


class _FakeAppbarUpdater:
    def __init__(self) -> None:
        self.last: str | None = None

    def update(self, message: str) -> None:
        self.last = message


def _log(tmp_path: Path) -> tuple[DailyLog, _FakeAppbarUpdater]:
    # bypass ToolKit.__init__ (flet.Page + live dpd.db) — DailyLog only ever
    # reads toolkit.paths and calls toolkit.appbar_updater.update(...).
    toolkit = object.__new__(ToolKit)
    paths = Gui2Paths(base_dir=tmp_path)
    # gui2/data is a tracked, always-present directory in production; DailyLog
    # relies on that and doesn't mkdir it itself, so the test sandbox must.
    paths.gui2_data_path.mkdir(parents=True, exist_ok=True)
    toolkit.paths = paths
    appbar_updater = _FakeAppbarUpdater()
    toolkit.appbar_updater = appbar_updater  # type: ignore[assignment]
    return DailyLog(toolkit), appbar_updater


class TestInitialState:
    def test_missing_file_starts_at_zero(self, tmp_path: Path):
        log, _ = _log(tmp_path)
        assert log.get_count("pass1") == 0
        assert log.get_history() == {}


class TestIncrement:
    def test_increments_default_amount(self, tmp_path: Path):
        log, _ = _log(tmp_path)
        log.increment("pass1")
        assert log.get_count("pass1") == 1

    def test_increments_by_given_count(self, tmp_path: Path):
        log, _ = _log(tmp_path)
        log.increment("pass1")
        log.increment("pass1", 2)
        assert log.get_count("pass1") == 3

    def test_invalid_key_raises(self, tmp_path: Path):
        log, _ = _log(tmp_path)
        try:
            log.increment("not_a_real_key")
        except ValueError:
            pass
        else:
            raise AssertionError("expected ValueError")

    def test_notifies_appbar_updater(self, tmp_path: Path):
        log, appbar_updater = _log(tmp_path)
        log.increment("pass1")
        assert appbar_updater.last == log.get_counts()

    def test_persists_across_reload(self, tmp_path: Path):
        log, _ = _log(tmp_path)
        log.increment("pass2_pre")
        reloaded, _ = _log(tmp_path)
        assert reloaded.get_count("pass2_pre") == 1


class TestGetCounts:
    def test_formats_all_keys(self, tmp_path: Path):
        log, _ = _log(tmp_path)
        log.increment("pass1")
        log.increment("pass2x", 2)
        counts = log.get_counts()
        assert "pass1: 1" in counts
        assert "pass2x: 2" in counts
