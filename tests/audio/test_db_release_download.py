import os
import sqlite3
import tarfile
from contextlib import closing
from pathlib import Path

import pytest

import audio.db_release_download as dl

ASSET_NAME = "dpd_audio_v0.0.1.tar.gz"


class FakeResponse:
    def __init__(self, data: bytes) -> None:
        self.data = data
        self.headers = {"content-length": str(len(data))}

    def raise_for_status(self) -> None:
        pass

    def iter_content(self, chunk_size: int):
        for i in range(0, len(self.data), chunk_size):
            yield self.data[i : i + chunk_size]


def make_archive(build_dir: Path, rows: int) -> bytes:
    """A gzipped tar holding dpd_audio.db with the given number of rows."""
    db_path = build_dir / "dpd_audio.db"
    with closing(sqlite3.connect(db_path)) as conn:
        conn.execute("CREATE TABLE dpd_audio (lemma_clean TEXT)")
        conn.executemany(
            "INSERT INTO dpd_audio VALUES (?)", [("word",) for _ in range(rows)]
        )
        # Random padding keeps the archive above the download's minimum size.
        conn.execute("CREATE TABLE padding (data BLOB)")
        conn.execute("INSERT INTO padding VALUES (?)", (os.urandom(4000),))
        conn.commit()
    archive = build_dir / ASSET_NAME
    with tarfile.open(archive, "w:gz") as tar:
        tar.add(db_path, arcname="dpd_audio.db")
    return archive.read_bytes()


@pytest.fixture
def audio_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    audio_dir = tmp_path / "audio_db"
    audio_dir.mkdir()
    live_db = audio_dir / "dpd_audio.db"
    live_db.write_text("old live db")
    monkeypatch.setattr(dl.pth, "dpd_audio_db_path", live_db)
    monkeypatch.setattr(
        dl,
        "get_latest_release",
        lambda: {"assets": [{"name": ASSET_NAME, "browser_download_url": "x"}]},
    )
    monkeypatch.setattr(dl, "find_index_asset", lambda info: {})
    monkeypatch.setattr(dl, "download_index", lambda asset: None)
    return audio_dir


def serve(monkeypatch: pytest.MonkeyPatch, data: bytes) -> None:
    monkeypatch.setattr(dl.requests, "get", lambda *a, **k: FakeResponse(data))


def test_good_db_replaces_live_db_and_leaves_nothing_behind(
    tmp_path: Path, audio_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    serve(monkeypatch, make_archive(tmp_path, rows=3))

    assert dl.main() is True

    with closing(sqlite3.connect(audio_dir / "dpd_audio.db")) as conn:
        assert conn.execute("SELECT COUNT(*) FROM dpd_audio").fetchone()[0] == 3
    assert sorted(p.name for p in audio_dir.iterdir()) == ["dpd_audio.db"]


def test_empty_db_keeps_live_db_and_leaves_nothing_behind(
    tmp_path: Path, audio_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    serve(monkeypatch, make_archive(tmp_path, rows=0))

    assert dl.main() is False

    assert (audio_dir / "dpd_audio.db").read_text() == "old live db"
    assert sorted(p.name for p in audio_dir.iterdir()) == ["dpd_audio.db"]
