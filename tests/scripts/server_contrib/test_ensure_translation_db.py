"""ensure_translation_db exits 0 only when the database file exists afterwards."""

from pathlib import Path

import pytest

from scripts.server_contrib import ensure_translation_db


class _Paths:
    def __init__(self, path: Path, zip_path: Path | None = None) -> None:
        self.tipitaka_translation_db_path = path
        self.tipitaka_translation_db_tarball = zip_path or path.with_suffix(".db.zip")


def test_exit_zero_when_the_database_is_there(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    db = tmp_path / "translations.db"
    db.write_bytes(b"x")
    monkeypatch.setattr(ensure_translation_db, "ensure_db_exists", lambda: None)
    monkeypatch.setattr(ensure_translation_db, "ProjectPaths", lambda: _Paths(db))

    assert ensure_translation_db.main() == 0


def test_exit_one_when_the_database_is_still_missing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(ensure_translation_db, "ensure_db_exists", lambda: None)
    monkeypatch.setattr(
        ensure_translation_db, "ProjectPaths", lambda: _Paths(tmp_path / "none.db")
    )

    assert ensure_translation_db.main() == 1


def test_it_downloads_before_it_checks(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    db = tmp_path / "translations.db"
    monkeypatch.setattr(
        ensure_translation_db, "ensure_db_exists", lambda: db.write_bytes(b"x")
    )
    monkeypatch.setattr(ensure_translation_db, "ProjectPaths", lambda: _Paths(db))

    assert ensure_translation_db.main() == 0


def test_a_broken_zip_is_deleted_and_the_download_is_tried_again(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    db = tmp_path / "translations.db"
    zip_path = tmp_path / "translations.db.zip"
    zip_path.write_bytes(b"half a download")
    zip_present_at_each_call: list[bool] = []

    def fake_ensure() -> None:
        zip_present_at_each_call.append(zip_path.exists())
        if not zip_path.exists():
            db.write_bytes(b"x")

    monkeypatch.setattr(ensure_translation_db, "ensure_db_exists", fake_ensure)
    monkeypatch.setattr(
        ensure_translation_db, "ProjectPaths", lambda: _Paths(db, zip_path)
    )

    assert ensure_translation_db.main() == 0
    assert zip_present_at_each_call == [True, False]


def test_the_zip_is_kept_when_the_database_arrived(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    db = tmp_path / "translations.db"
    db.write_bytes(b"x")
    zip_path = tmp_path / "translations.db.zip"
    zip_path.write_bytes(b"a good zip")
    calls: list[int] = []
    monkeypatch.setattr(
        ensure_translation_db, "ensure_db_exists", lambda: calls.append(1)
    )
    monkeypatch.setattr(
        ensure_translation_db, "ProjectPaths", lambda: _Paths(db, zip_path)
    )

    assert ensure_translation_db.main() == 0
    assert zip_path.exists()
    assert len(calls) == 1


def test_it_gives_up_after_one_retry(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    db = tmp_path / "translations.db"
    calls: list[int] = []
    monkeypatch.setattr(
        ensure_translation_db, "ensure_db_exists", lambda: calls.append(1)
    )
    monkeypatch.setattr(ensure_translation_db, "ProjectPaths", lambda: _Paths(db))

    assert ensure_translation_db.main() == 1
    assert len(calls) == 2
