"""Characterisation test locking ``get_passage_by_code`` output across the
cst_source refactor.

``passage_by_code.py`` drove the old ``GlobalData`` + bare per-book handlers
directly; the refactor replaces that with the new parser API. The baseline
fixture was captured from the pre-refactor code; output must stay identical.

Covers all four prose parsers (DN/MN/SN/AN) plus a verse code (DHP).
"""

import json
from dataclasses import asdict
from pathlib import Path

import pytest

from exporter.analysis.passage_by_code import get_passage_by_code

FIXTURE = Path(__file__).parent / "fixtures" / "passage_by_code_baseline.json"
BASELINE: dict[str, dict] = json.loads(FIXTURE.read_text(encoding="utf-8"))

# Parses full nikāya XML — slow; deselected from the default run.
pytestmark = pytest.mark.slow


@pytest.mark.parametrize("code", sorted(BASELINE))
def test_passage_by_code_matches_baseline(code: str) -> None:
    expected = BASELINE[code]
    assert "__error__" not in expected, f"baseline for {code} captured an error"
    result = asdict(get_passage_by_code(code))
    assert result == expected
