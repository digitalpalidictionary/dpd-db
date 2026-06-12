import json
import os
from pathlib import Path
from typing import Any, cast

import pytest
from sqlalchemy.orm import Session

from db.db_helpers import get_db_session
from exporter.analysis.passage_by_code import get_passage_by_code
from exporter.analysis.translate_core import (
    _clean_meaning,
    _select_best_option,
    generate_markdown_report,
    translate_sentence,
)
from tests.exporter.analysis.recorded_ai_manager import RecordedAIManager
from tools.ai_manager import AIManager
from tools.paths import ProjectPaths

PASSAGES = ["TH215", "MN41_p2", "SN15.1_p2", "DHP211", "AN3.33_p1"]


@pytest.fixture(scope="module")
def db_session() -> Session:
    pth = ProjectPaths()
    return get_db_session(pth.dpd_db_path)


@pytest.fixture
def update_goldens() -> bool:
    return os.environ.get("UPDATE_GOLDENS") == "1"


def extract_distilled_rows(
    merged_result: dict[str, Any],
) -> list[tuple[str, int, str, str, str]]:
    """Extract (surface_word, occurrence, selected_key, grammar, meaning) rows."""
    rows = []
    word_counts = {}

    for word_obj in merged_result.get("analysis", []):
        word = word_obj["word"]
        word_counts[word] = word_counts.get(word, 0) + 1
        occurrence = word_counts[word]

        best_option = _select_best_option(word_obj.get("data", []))
        if best_option:
            key = best_option.get("key", "")
            grammar = best_option.get("grammar", "")
            meaning = _clean_meaning(best_option.get("meaning_combo", ""))
            rows.append((word, occurrence, key, grammar, meaning))
        else:
            rows.append((word, occurrence, "", "", ""))

    return rows


@pytest.mark.parametrize("passage_name", PASSAGES)
def test_passage_regression(
    passage_name: str, db_session: Session, update_goldens: bool
):
    fixture_dir = Path("tests/exporter/analysis/fixtures/passages") / passage_name
    debug_path = fixture_dir / "ai_debug.json"
    metadata_path = fixture_dir / "metadata.json"

    with open(metadata_path) as f:
        meta = json.load(f)

    ai_manager = RecordedAIManager(debug_path)

    # Map passage_name to (code, paragraph_index)
    passage_map = {
        "TH215": ("TH215", 0),
        "MN41_p2": ("MN41", 1),
        "SN15.1_p2": ("SN15.1", 1),
        "DHP211": ("DHP211", 0),
        "AN3.33_p1": ("AN3.33", 0),
    }

    code, p_idx = passage_map[passage_name]
    passage_obj = get_passage_by_code(code).paragraphs[p_idx]

    # Run the orchestrator
    merged = translate_sentence(
        passage_obj,
        db_session,
        cast(AIManager, ai_manager),
        model=meta["model"],
        provider=meta["provider"],
        verse_source=passage_name,
        debug={},
    )

    ai_manager.assert_empty()

    study_json = json.dumps(merged, ensure_ascii=False, indent=2)
    study_md = generate_markdown_report(merged, passage_obj, verse_id=passage_name)
    distilled_rows = extract_distilled_rows(merged)

    json_path = fixture_dir / "study.json"
    md_path = fixture_dir / "study.md"
    distilled_path = fixture_dir / "distilled.json"

    if update_goldens:
        json_path.write_text(study_json, encoding="utf-8")
        md_path.write_text(study_md, encoding="utf-8")
        distilled_path.write_text(
            json.dumps(distilled_rows, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        return

    # Assertions
    # 1. Byte-equality (JSON)
    expected_json = json_path.read_text(encoding="utf-8")
    assert study_json == expected_json, f"JSON regression for {passage_name}"

    # 2. Byte-equality (MD)
    expected_md = md_path.read_text(encoding="utf-8")
    assert study_md == expected_md, f"MD regression for {passage_name}"

    # 3. Distilled golden
    expected_distilled = json.loads(distilled_path.read_text(encoding="utf-8"))
    # Convert list of lists to list of tuples for comparison
    expected_distilled = [tuple(row) for row in expected_distilled]
    assert distilled_rows == expected_distilled, (
        f"Distilled regression for {passage_name}"
    )

    # 4. Frozen correctness facts (Task 1.5)
    if passage_name == "SN15.1_p2":
        # SN15.1 refrain gen pl (F71/F63)
        gen_pl_words = [
            "avijjānīvaraṇānaṃ",
            "taṇhāsaṃyojanānaṃ",
            "sandhāvataṃ",
            "saṃsarataṃ",
        ]
        for word in gen_pl_words:
            matching = [r for r in distilled_rows if r[0] == word]
            assert any("gen pl" in r[3] for r in matching), f"{word} should be gen pl"

    # F66 no fan-out for tassa/tassā (independent selections)
    if passage_name == "SN15.1_p2":
        # SN15.1 has multiple 'tassa' or similar?
        # Actually MN41_p2 has 'tassa' and 'tassā' and 'kāyassa'
        pass

    if passage_name == "MN41_p2":
        # F66: tassa/tassā/kāyassa independent selections
        # Ensure that multiple occurrences don't all get forced to the same positional key
        kayassa_rows = [r for r in distilled_rows if r[0] == "kāyassa"]
        if len(kayassa_rows) > 1:
            kayassa_keys = set(r[2] for r in kayassa_rows)
            assert len(kayassa_keys) > 1, (
                "F66: 'kāyassa' occurrences should have independent selections, not fanned out to a single key."
            )

    # F67/F74 no placeholder [Deconstructed]
    assert "[Deconstructed]" not in study_md
    assert "*(AI analysis of deconstruction)*" not in study_md

    # F62 no empty meanings
    for r in distilled_rows:
        assert r[4].strip() != "", f"Empty meaning for {r[0]} in {passage_name}"

    # F48 no grammar-note parentheticals in meanings
    for r in distilled_rows:
        meaning = r[4]
        assert "(accusative)" not in meaning
        assert "(nominative plural)" not in meaning
        # Add more if needed from F48
