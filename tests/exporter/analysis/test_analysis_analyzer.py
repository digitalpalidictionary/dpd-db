"""Verify basic tokenizer and analyzer behavior in the analysis package."""

from types import SimpleNamespace
from typing import cast, get_type_hints

from db.models import DpdHeadword
from exporter.analysis.analyzer import (
    _normalize_kammadharaya_construction,
    get_completeness,
    get_grammar_from_inflections_html,
    get_in_comp_forms,
    is_pos_compatible,
    is_stem_compatible,
    root_combo,
    tokenize_sentence,
)


def _collect_analysis_keys(options: list[dict[str, object]]) -> list[str]:
    keys: list[str] = []
    for option in options:
        key = option.get("key")
        if isinstance(key, str):
            keys.append(key)
        components = option.get("components")
        if not isinstance(components, list):
            continue
        for component_group in components:
            if isinstance(component_group, list):
                keys.extend(_collect_analysis_keys(component_group))
    return keys


def test_normalize_kammadharaya_construction() -> None:
    assert _normalize_kammadharaya_construction("paññā eva āvudha") == "paññā + āvudha"
    assert _normalize_kammadharaya_construction("īsā viya danta") == "īsā + danta"
    assert (
        _normalize_kammadharaya_construction("icchā nidānaṃ etassa")
        == "icchā + nidānaṃ"
    )
    assert _normalize_kammadharaya_construction("paññā + āvudha") == "paññā + āvudha"
    assert _normalize_kammadharaya_construction("paññā āvudha") == "paññā + āvudha"
    assert _normalize_kammadharaya_construction("paññā") == "paññā"


def test_tokenize_sentence_basic() -> None:
    sentence = "Evaṃ me sutaṃ."
    tokens = tokenize_sentence(sentence)
    assert tokens == ["evaṃ", "me", "sutaṃ"]


def test_tokenize_sentence_punctuation() -> None:
    sentence = "Namo tassa bhagavato, arahato, sammāsambuddhassa!"
    tokens = tokenize_sentence(sentence)
    assert tokens == ["namo", "tassa", "bhagavato", "arahato", "sammāsambuddhassa"]


def test_tokenize_sentence_empty() -> None:
    assert tokenize_sentence("") == []
    assert tokenize_sentence("   ") == []


def test_helper_return_annotations_present() -> None:
    assert get_type_hints(get_completeness)["return"] == tuple[int, str]
    assert get_type_hints(root_combo)["return"] is str


def test_get_completeness_complete() -> None:
    headword = cast(DpdHeadword, SimpleNamespace(meaning_1="test", source_1="SN1.1"))

    assert get_completeness(headword) == (2, "complete")


def test_get_completeness_semi_complete() -> None:
    headword = cast(DpdHeadword, SimpleNamespace(meaning_1="test", source_1=""))

    assert get_completeness(headword) == (1, "semi-complete")


def test_get_completeness_incomplete() -> None:
    headword = cast(DpdHeadword, SimpleNamespace(meaning_1="", source_1="SN1.1"))

    assert get_completeness(headword) == (0, "incomplete")


def test_root_combo_with_root() -> None:
    root = SimpleNamespace(root_group="1", root_meaning="to go")
    headword = cast(
        DpdHeadword,
        SimpleNamespace(
            rt=root,
            root_clean="√gam",
            root_sign="gacchati",
        ),
    )

    assert root_combo(headword) == "√gam 1 gacchati (to go)"


def test_root_combo_without_root() -> None:
    headword = cast(DpdHeadword, SimpleNamespace(rt=None))

    assert root_combo(headword) == ""


def test_is_stem_compatible_in_comp() -> None:
    assert is_stem_compatible("masc in comp") is True


def test_is_stem_compatible_inflected() -> None:
    assert is_stem_compatible("masc nom sg") is False


def test_is_stem_compatible_no_case() -> None:
    assert is_stem_compatible("adj") is True


def test_get_in_comp_forms_found() -> None:
    html = "<tr><th>in comps</th><td>dhamma<br>buddha</td></tr>"

    assert get_in_comp_forms(html) == {"dhamma", "buddha"}


def test_get_in_comp_forms_not_found() -> None:
    html = "<tr><th>nom sg</th><td>dhammo</td></tr>"

    assert get_in_comp_forms(html) == set()


def test_get_grammar_from_inflections_html_found() -> None:
    html = "<tr><td title='masc acc sg'>dhammaṃ</td></tr>"
    headword = cast(
        DpdHeadword,
        SimpleNamespace(lemma_clean="dhamma", inflections_html=html),
    )

    assert get_grammar_from_inflections_html("dhammaṃ", headword) == (
        "masc acc sg of dhamma"
    )


def test_get_grammar_from_inflections_html_not_found() -> None:
    html = "<tr><td title='masc acc sg'>dhammaṃ</td></tr>"
    headword = cast(
        DpdHeadword,
        SimpleNamespace(lemma_clean="dhamma", inflections_html=html),
    )

    assert get_grammar_from_inflections_html("buddhaṃ", headword) is None


def test_analyze_sentence_keys_are_unique_per_word_occurrence() -> None:
    from db.db_helpers import get_db_session
    from exporter.analysis.analyzer import analyze_sentence
    from exporter.mcp.config import mcp_config

    db_session = get_db_session(mcp_config.db_path)

    try:
        results = analyze_sentence("tassa tassa", db_session)
    finally:
        db_session.close()

    keys = [
        key
        for token_data in results
        for key in _collect_analysis_keys(
            cast(list[dict[str, object]], token_data["data"])
        )
    ]

    assert keys
    assert len(keys) == len(set(keys))


def test_is_pos_compatible_exact_match() -> None:
    assert is_pos_compatible("masc", "masc") is True


def test_is_pos_compatible_noun_gender() -> None:
    assert is_pos_compatible("masc", "noun") is True


def test_is_pos_compatible_verb_tense() -> None:
    assert is_pos_compatible("aor", "verb") is True


def test_is_pos_compatible_mismatch() -> None:
    assert is_pos_compatible("masc", "verb") is False


def test_analyze_sentence() -> None:
    # This test requires a valid dpd.db to be present at the expected path.
    from exporter.analysis.analyzer import analyze_sentence
    from db.db_helpers import get_db_session
    from exporter.mcp.config import mcp_config

    db_session = get_db_session(mcp_config.db_path)

    sentence = "Evaṃ me sutaṃ."
    results = analyze_sentence(sentence, db_session)

    assert len(results) == 3
    # Check "evaṃ"
    assert results[0]["word"] == "evaṃ"
    assert "lemma" in results[0]["data"][0]

    # Check "me"
    assert results[1]["word"] == "me"

    # Check "sutaṃ"
    assert results[2]["word"] == "sutaṃ"


def test_analyze_sentence_not_found() -> None:
    from exporter.analysis.analyzer import analyze_sentence
    from db.db_helpers import get_db_session
    from exporter.mcp.config import mcp_config

    db_session = get_db_session(mcp_config.db_path)

    # Using a string that is Pāḷi-alphabet-only but unlikely to be in the dictionary
    sentence = "abbcccddd"
    results = analyze_sentence(sentence, db_session)

    assert len(results) == 1
    assert results[0]["word"] == "abbcccddd"
    assert results[0]["status"] == "not_found"
