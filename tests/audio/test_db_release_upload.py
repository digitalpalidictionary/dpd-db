from pathlib import Path
from unittest.mock import MagicMock

import audio.db_release_upload as module


def _mock_pth(tmp_path: Path) -> MagicMock:
    mock = MagicMock()
    mock.dpd_audio_db_path = tmp_path / "dpd_audio.db"
    return mock


def test_get_archive_path_exists(tmp_path: Path) -> None:
    pth = _mock_pth(tmp_path)
    version = "v0.1.260601"
    (tmp_path / f"dpd_audio_{version}.tar.gz").touch()
    result = module.get_archive_path(pth, version)
    assert result == tmp_path / f"dpd_audio_{version}.tar.gz"


def test_get_archive_path_missing(tmp_path: Path) -> None:
    assert module.get_archive_path(_mock_pth(tmp_path), "v9.9.9") is None


def test_get_index_path_exists(tmp_path: Path) -> None:
    pth = _mock_pth(tmp_path)
    version = "v0.1.260601"
    (tmp_path / f"dpd_audio_index_{version}.tsv").touch()
    result = module.get_index_path(pth, version)
    assert result == tmp_path / f"dpd_audio_index_{version}.tsv"


def test_get_index_path_missing(tmp_path: Path) -> None:
    assert module.get_index_path(_mock_pth(tmp_path), "v9.9.9") is None
