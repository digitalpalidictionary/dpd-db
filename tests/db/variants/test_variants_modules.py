import json
from pathlib import Path

import pytest

from db.variants.variants_modules import (
    VariantsDict,
    context_cleaner,
    key_cleaner,
    normalize_pali_text,
    save_json,
)

FIXTURE_PATH = Path(__file__).parent / "test_variants_modules_fixtures.json"


@pytest.fixture(scope="module")
def fixtures() -> dict:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


@pytest.mark.parametrize(
    "case",
    [
        "pure_pali",
        "uppercase",
        "spaces",
        "non_pali_chars",
        "pali_diacritics",
        "diacritics_lower",
        "mixed",
        "empty",
    ],
)
def test_key_cleaner(fixtures: dict, case: str) -> None:
    data = fixtures["key_cleaner"][case]
    assert key_cleaner(data["input"]) == data["output"]


@pytest.mark.parametrize(
    "case",
    [
        "single_quote",
        "double_quote_curly",
        "double_quote_straight",
        "parentheses",
        "asterisk",
        "digits",
        "leading_dot",
        "trailing_dot",
        "uppercase",
        "clean",
        "empty",
        "combined",
    ],
)
def test_context_cleaner(fixtures: dict, case: str) -> None:
    data = fixtures["context_cleaner"][case]
    assert context_cleaner(data["input"]) == data["output"]


@pytest.mark.parametrize(
    "text,expected",
    [
        ("saraṇagamanaṁ", "saraṇagamanaṃ"),
        ("ayaṁ pāṭho saṁyutta", "ayaṃ pāṭho saṃyutta"),
        ("dhammaṃ", "dhammaṃ"),
        ("", ""),
    ],
)
def test_normalize_pali_text(text: str, expected: str) -> None:
    assert normalize_pali_text(text) == expected


def test_normalize_pali_text_output_survives_key_cleaner() -> None:
    """key_cleaner's character set lacks ṁ — normalization must restore ṃ first."""
    assert key_cleaner(normalize_pali_text("saraṇagamanaṁ")) == "saraṇagamanaṃ"
    assert key_cleaner("saraṇagamanaṁ") == "saraṇagamana"


def test_save_json_writes_correct_content(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    (tmp_path / "temp").mkdir()
    monkeypatch.chdir(tmp_path)
    variants: VariantsDict = {
        "anicca": {"cst": {"dn1": [("sabbe saṅkhārā", "aniccā")]}}
    }
    save_json(variants)
    result = json.loads(
        (tmp_path / "temp" / "variants.json").read_text(encoding="utf-8")
    )
    expected = json.loads(json.dumps(variants, ensure_ascii=False))
    assert result == expected
