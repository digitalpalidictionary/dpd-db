"""Tests for exporter/pdf/pdf_exporter.py."""

import importlib
import json
import re
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

FIXTURE_PATH = Path(__file__).parent / "test_pdf_exporter_fixtures.json"


@pytest.fixture(scope="module")
def fixtures() -> dict:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# 1. Import-time DB guard: importing the module must NOT open a DB connection
# ---------------------------------------------------------------------------


def test_import_does_not_open_db() -> None:
    """GlobalVars must not run get_db_session at class / import level."""
    call_count = 0

    real_get = None
    import db.db_helpers as _helpers

    real_get = _helpers.get_db_session

    def mock_get_db(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        return real_get(*args, **kwargs)

    with patch("db.db_helpers.get_db_session", side_effect=mock_get_db):
        import exporter.pdf.pdf_exporter  # noqa: F401

        importlib.reload(exporter.pdf.pdf_exporter)

    assert call_count == 0, (
        f"get_db_session was called {call_count} time(s) at import — "
        "GlobalVars must not open the DB at class level"
    )


# ---------------------------------------------------------------------------
# 2. Regex fix: [A-Z][A-Za-z] is byte-identical to [A-Z][A-z] on real data
# ---------------------------------------------------------------------------


def test_abbreviation_regex_byte_identical(fixtures: dict) -> None:
    """[A-Z][A-Za-z] must filter exactly the same abbrevs as the old [A-Z][A-z]."""
    rows = fixtures["abbreviations"]
    for row in rows:
        old_result = bool(re.findall(r"[A-Z][A-z]", row["abbrev"]))
        new_result = bool(re.findall(r"[A-Z][A-Za-z]", row["abbrev"]))
        assert new_result == old_result, (
            f"abbrev {row['abbrev']!r}: old={old_result}, new={new_result}"
        )


def test_abbreviation_regex_filtered_count(fixtures: dict) -> None:
    """Exactly 121 of 224 abbrevs are filtered out (book names with double capital)."""
    rows = fixtures["abbreviations"]
    filtered = sum(1 for r in rows if re.findall(r"[A-Z][A-Za-z]", r["abbrev"]))
    assert filtered == 121


# ---------------------------------------------------------------------------
# 3. save_typist_file writes UTF-8 with Pāḷi diacritics intact
# ---------------------------------------------------------------------------


def test_save_typist_file_encoding() -> None:
    """save_typist_file must write UTF-8 so Pāḷi diacritics round-trip correctly."""
    from exporter.pdf.pdf_exporter import save_typist_file

    pali_content = "Namo tassa bhagavato arahato sammāsambuddhassa\n"

    g = MagicMock()
    g.typst_data = [pali_content]

    with tempfile.NamedTemporaryFile(suffix=".typ", delete=False) as tmp:
        tmp_path = Path(tmp.name)

    try:
        g.pth.typst_lite_data_path = tmp_path
        save_typist_file(g)
        written = tmp_path.read_text(encoding="utf-8")
        assert written == pali_content
    finally:
        tmp_path.unlink(missing_ok=True)
