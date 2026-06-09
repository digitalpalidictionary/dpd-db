"""Golden-master test for tools/docs_update_bibliography.py.

The fixture freezes the markdown produced by the build at the time of the
refactor (captured from the current code and verified byte-identical to the
published docs/bibliography.md). The refactored make_bibliography_md must
reproduce it exactly.
"""

import json
from pathlib import Path

from tools.docs_update_bibliography import make_bibliography_md
from tools.paths import ProjectPaths

FIXTURE_PATH = Path(__file__).parent / "test_docs_update_bibliography_fixtures.json"


def test_make_bibliography_md_matches_golden_master() -> None:
    fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    pth = ProjectPaths()
    assert make_bibliography_md(pth) == fixture["bibliography_md"]
