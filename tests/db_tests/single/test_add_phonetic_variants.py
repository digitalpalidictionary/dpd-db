"""Tests for db_tests/single/add_phonetic_variants.py"""

from types import SimpleNamespace
from typing import Any

from tools.synonym_variant import (
    PhoneticVariantDetector,
    assign_relationship as _assign,
)


def make_hw(
    lemma_1: str,
    id: int | None = None,
    lemma_clean: str | None = None,
    pos: str = "verb",
    construction_clean: str = "",
    root_base_clean: str = "",
    family_word: str = "",
    family_root: str = "",
    root_key: str = "",
    root_sign: str = "",
    meaning_1: str = "x",
    meaning_combo: str = "",
    var_phonetic: str = "",
    var_text: str = "",
    variant: str = "",
    synonym: str = "",
) -> Any:
    return SimpleNamespace(
        id=id,
        lemma_1=lemma_1,
        lemma_clean=lemma_clean if lemma_clean is not None else lemma_1,
        pos=pos,
        construction_clean=construction_clean,
        root_base_clean=root_base_clean,
        family_word=family_word,
        family_root=family_root,
        root_key=root_key,
        root_sign=root_sign,
        meaning_1=meaning_1,
        meaning_combo=meaning_combo,
        var_phonetic=var_phonetic,
        var_text=var_text,
        variant=variant,
        synonym=synonym,
        synonym_list=synonym.split(", ") if synonym else [],
        freq_data_unpack={},
    )


def _pairs_of(results: list[tuple[Any, str, str]]) -> set[tuple[str, str]]:
    return {(r[0].lemma_1, r[1]) for r in results}


def _rules_of(results: list[tuple[Any, str, str]]) -> set[str]:
    return {r[2] for r in results}


def test_assign_synonym_removes_phonetic_textual_and_variant() -> None:
    hw = make_hw("foo", synonym="", var_phonetic="bar", variant="bar", var_text="bar")
    _assign(hw, "bar", "synonym")
    assert hw.synonym == "bar"
    assert hw.var_phonetic == ""
    assert hw.var_text == ""
    assert hw.variant == ""


def test_assign_phonetic_removes_synonym_textual_and_variant() -> None:
    hw = make_hw("foo", synonym="bar", var_phonetic="", variant="bar", var_text="bar")
    _assign(hw, "bar", "var_phonetic")
    assert hw.synonym == ""
    assert hw.var_phonetic == "bar"
    assert hw.var_text == ""
    assert hw.variant == ""


def test_assign_textual_removes_synonym_phonetic_and_variant() -> None:
    hw = make_hw("foo", synonym="bar", var_phonetic="bar", variant="bar", var_text="")
    _assign(hw, "bar", "var_text")
    assert hw.synonym == ""
    assert hw.var_phonetic == ""
    assert hw.var_text == "bar"
    assert hw.variant == ""


# ---- same_construction ----


def test_same_construction_finds_pair() -> None:
    a = make_hw("jeti", construction_clean="ji + *a", pos="verb")
    b = make_hw("jayati", construction_clean="ji + *a", pos="verb")
    lonely = make_hw("gacchati", construction_clean="gam + *a", pos="verb")

    detector = PhoneticVariantDetector([a, b, lonely])
    results = detector.detect_same_construction()

    assert ("jeti", "jayati") in _pairs_of(results)
    assert ("jayati", "jeti") in _pairs_of(results)
    assert all("gacchati" not in (r[0].lemma_1, r[1]) for r in results)
    assert all(r[2] == "same_construction" for r in results)


def test_same_construction_ignores_empty() -> None:
    a = make_hw("foo", construction_clean="", pos="noun")
    b = make_hw("bar", construction_clean="", pos="noun")
    assert PhoneticVariantDetector([a, b]).detect_same_construction() == []


def test_same_construction_surfaces_inconsistent_recording() -> None:
    # Inconsistent: a says phon, b says nothing. Raw detector should still
    # propose both directions so the pair surfaces in the canonical layer.
    a = make_hw("jeti", construction_clean="ji + *a", pos="verb", var_phonetic="jayati")
    b = make_hw("jayati", construction_clean="ji + *a", pos="verb")
    results = PhoneticVariantDetector([a, b]).detect_same_construction()
    assert any(r[0].lemma_1 == "jeti" for r in results)
    assert any(r[0].lemma_1 == "jayati" for r in results)


# ---- detect_by_rules ----


def test_rules_e_aya_matches() -> None:
    a = make_hw("jayati")
    b = make_hw("jeti")
    results = PhoneticVariantDetector([a, b]).detect_by_rules()
    assert "rule:e<->aya" in _rules_of(results)
    assert ("jayati", "jeti") in _pairs_of(results)


def test_rules_t_retroflex_matches() -> None:
    a = make_hw("akaṭa")
    b = make_hw("akata")
    results = PhoneticVariantDetector([a, b]).detect_by_rules()
    assert "rule:t<->ṭ" in _rules_of(results)


def test_rules_surfaces_inconsistent_recording() -> None:
    # Inconsistent one-sided var_phonetic: surface so the user can fix it.
    a = make_hw("akaṭa", var_phonetic="akata")
    b = make_hw("akata")
    results = PhoneticVariantDetector([a, b]).detect_by_rules()
    assert any(r[0].lemma_1 == "akaṭa" for r in results)


# ---- detect_base_e_aya ----


def test_detect_base_e_aya_finds_pair() -> None:
    a = make_hw(
        "jeti",
        construction_clean="ji + *a",
        pos="verb",
        root_base_clean="ji > ji + e",
        root_key="ji_1",
        family_root="ji",
        root_sign="*e",
    )
    b = make_hw(
        "jayati",
        construction_clean="ji + *a",
        pos="verb",
        root_base_clean="ji > ji + aya",
        root_key="ji_1",
        family_root="ji",
        root_sign="*aya",
    )
    results = PhoneticVariantDetector([a, b]).detect_base_e_aya()
    assert ("jeti", "jayati") in _pairs_of(results) or ("jayati", "jeti") in _pairs_of(
        results
    )
    assert all(r[2] == "base:e<->aya" for r in results)


# ---- detect_base_ya_iya_iiya ----


def test_detect_base_ya_iya_iiya_finds_pair() -> None:
    a = make_hw(
        "yāciyamāna",
        construction_clean="yāc + *iya + māna",
        pos="ptp",
        root_base_clean="yāc > yāci + iya",
        root_key="yāc_1",
        family_root="yāc",
        root_sign="iya",
    )
    b = make_hw(
        "yācīyamāna",
        construction_clean="yāc + *iya + māna",
        pos="ptp",
        root_base_clean="yāc > yāci + īya",
        root_key="yāc_1",
        family_root="yāc",
        root_sign="īya",
    )
    results = PhoneticVariantDetector([a, b]).detect_base_ya_iya_iiya()
    pairs = _pairs_of(results)
    assert ("yāciyamāna", "yācīyamāna") in pairs or (
        "yācīyamāna",
        "yāciyamāna",
    ) in pairs
    assert all(r[2] == "base:ya<->iya<->īya" for r in results)


# ---- canonical pairs ----


def test_canonical_pairs_collapses_symmetric() -> None:
    a = make_hw("jeti", construction_clean="ji + *a", pos="verb", family_word="ji")
    b = make_hw("jayati", construction_clean="ji + *a", pos="verb", family_word="ji")
    detector = PhoneticVariantDetector([a, b])
    pairs = detector.detect_canonical_pairs([])
    sc = [p for p in pairs if p.rule == "same_construction"]
    assert len(sc) == 1
    assert sc[0].source.lemma_1 == "jeti"
    assert sc[0].target.lemma_1 == "jayati"


def test_canonical_pairs_respects_exceptions() -> None:
    a = make_hw("jeti", id=10, construction_clean="ji + *a", pos="verb")
    b = make_hw("jayati", id=11, construction_clean="ji + *a", pos="verb")
    exc_key = "10:verb|11:verb"
    detector = PhoneticVariantDetector([a, b])
    pairs = detector.detect_canonical_pairs([exc_key])
    sc = [p for p in pairs if p.rule == "same_construction"]
    assert sc == []


def test_canonical_pairs_drops_already_related() -> None:
    a = make_hw(
        "jeti",
        construction_clean="ji + *a",
        pos="verb",
        var_phonetic="jayati",
    )
    b = make_hw(
        "jayati",
        construction_clean="ji + *a",
        pos="verb",
        var_phonetic="jeti",
    )
    pairs = PhoneticVariantDetector([a, b]).detect_canonical_pairs([])
    assert pairs == []


def test_canonical_pairs_reject_different_pos() -> None:
    a = make_hw("aḍḍa", pos="masc")
    b = make_hw("adda 1.1", lemma_clean="adda", pos="aor")
    detector = PhoneticVariantDetector([a, b])
    pairs = detector.detect_canonical_pairs([])
    assert pairs == []


def test_canonical_pairs_allow_masc_nt() -> None:
    # t↔ṭ rule: kūṭa masc ↔ kūta nt — masc/nt treated as the same class
    a = make_hw("kūṭa", lemma_clean="kūṭa", pos="masc")
    b = make_hw("kūta", lemma_clean="kūta", pos="nt")
    detector = PhoneticVariantDetector([a, b])
    pairs = detector.detect_canonical_pairs([])
    assert len(pairs) >= 1


def test_canonical_pairs_reject_masc_fem() -> None:
    # t↔ṭ rule: same phonetic pair but masc/fem — should be rejected
    a = make_hw("kūṭa", lemma_clean="kūṭa", pos="masc")
    b = make_hw("kūta", lemma_clean="kūta", pos="fem")
    detector = PhoneticVariantDetector([a, b])
    pairs = detector.detect_canonical_pairs([])
    assert pairs == []


def test_canonical_pairs_reject_nt_fem() -> None:
    # t↔ṭ rule: same phonetic pair but nt/fem — should be rejected
    a = make_hw("kūṭa", lemma_clean="kūṭa", pos="nt")
    b = make_hw("kūta", lemma_clean="kūta", pos="fem")
    detector = PhoneticVariantDetector([a, b])
    pairs = detector.detect_canonical_pairs([])
    assert pairs == []


def test_canonical_pairs_reject_different_family_root() -> None:
    a = make_hw("dahati", id=1, lemma_clean="dahati", pos="verb", family_root="dah")
    b = make_hw("ḍahati", id=2, lemma_clean="ḍahati", pos="verb", family_root="ḍah")
    detector = PhoneticVariantDetector([a, b])
    pairs = detector.detect_canonical_pairs([])
    assert pairs == []


def test_canonical_pairs_allow_same_family_root() -> None:
    a = make_hw(
        "dahati",
        id=1,
        lemma_clean="dahati",
        pos="verb",
        root_key="dah_1",
        family_root="dah",
    )
    b = make_hw(
        "ḍahati",
        id=2,
        lemma_clean="ḍahati",
        pos="verb",
        root_key="dah_1",
        family_root="dah",
    )
    detector = PhoneticVariantDetector([a, b])
    pairs = detector.detect_canonical_pairs([])
    assert {(p.source.id, p.target.id) for p in pairs} == {(1, 2)}


def test_canonical_pairs_reject_different_root_key() -> None:
    a = make_hw(
        "kappayati",
        id=1,
        lemma_clean="kappayati",
        pos="verb",
        root_key="kapp_1",
        family_root="kapp",
    )
    b = make_hw(
        "kappeti 2",
        id=2,
        lemma_clean="kappeti",
        pos="verb",
        root_key="kapp_2",
        family_root="kapp",
    )
    detector = PhoneticVariantDetector([a, b])
    pairs = detector.detect_canonical_pairs([])
    assert pairs == []


def test_canonical_pairs_reject_different_family_word() -> None:
    a = make_hw("sadda", id=1, lemma_clean="sadda", pos="noun", family_word="sad")
    b = make_hw("saddha", id=2, lemma_clean="saddha", pos="noun", family_word="sidh")
    detector = PhoneticVariantDetector([a, b])
    pairs = detector.detect_canonical_pairs([])
    assert pairs == []


def test_canonical_pairs_reject_only_one_family_word() -> None:
    a = make_hw("sadda", id=1, lemma_clean="sadda", pos="noun", family_word="sad")
    b = make_hw("saddha", id=2, lemma_clean="saddha", pos="noun")
    detector = PhoneticVariantDetector([a, b])
    pairs = detector.detect_canonical_pairs([])
    assert pairs == []


def test_canonical_pairs_allow_same_family_word() -> None:
    a = make_hw("sadda", id=1, lemma_clean="sadda", pos="noun", family_word="sad")
    b = make_hw("saddha", id=2, lemma_clean="saddha", pos="noun", family_word="sad")
    detector = PhoneticVariantDetector([a, b])
    pairs = detector.detect_canonical_pairs([])
    assert {(p.source.id, p.target.id) for p in pairs} == {(1, 2)} or {
        (p.source.id, p.target.id) for p in pairs
    } == {(2, 1)}


def test_canonical_pairs_allow_when_both_families_empty() -> None:
    a = make_hw("akaṭa", id=1, lemma_clean="akaṭa", pos="adj")
    b = make_hw("akata", id=2, lemma_clean="akata", pos="adj")
    detector = PhoneticVariantDetector([a, b])
    pairs = detector.detect_canonical_pairs([])
    assert {(p.source.id, p.target.id) for p in pairs} == {(1, 2)}


def test_canonical_pairs_split_same_clean_targets_into_distinct_pairs() -> None:
    a = make_hw("sadda", construction_clean="sad + a", pos="noun")
    b = make_hw(
        "sadda_1", lemma_clean="saddha", construction_clean="sad + a", pos="noun"
    )
    c = make_hw(
        "sadda_2", lemma_clean="saddha", construction_clean="sad + a", pos="noun"
    )

    pairs = PhoneticVariantDetector([a, b, c]).detect_canonical_pairs([])
    same_construction = [p for p in pairs if p.rule == "same_construction"]

    assert len(same_construction) == 2
    assert {(p.source.lemma_1, p.target.lemma_1) for p in same_construction} == {
        ("sadda", "sadda_1"),
        ("sadda", "sadda_2"),
    }


def test_canonical_pairs_exception_is_exact_headword_pair() -> None:
    a = make_hw("dahati", id=100, lemma_clean="dahati", pos="verb")
    b = make_hw("ḍahati", id=101, lemma_clean="ḍahati", pos="verb")
    c = make_hw("ḍahati", id=102, lemma_clean="ḍahati", pos="verb")

    detector = PhoneticVariantDetector([a, b, c])
    pairs = detector.detect_canonical_pairs(["100:verb|101:verb"])

    assert {(p.source.id, p.target.id) for p in pairs} == {(100, 102)}


def test_canonical_pairs_prioritize_both_meaning_1() -> None:
    a = make_hw(
        "akaṭa",
        id=1,
        lemma_clean="akaṭa",
        pos="adj",
        meaning_1="meaning",
    )
    b = make_hw(
        "akata",
        id=2,
        lemma_clean="akata",
        pos="adj",
        meaning_1="meaning",
    )
    c = make_hw(
        "bar",
        id=3,
        lemma_clean="bar",
        pos="verb",
        construction_clean="x",
        meaning_1="",
    )
    d = make_hw(
        "baz",
        id=4,
        lemma_clean="baz",
        pos="verb",
        construction_clean="x",
        meaning_1="meaning",
    )

    pairs = PhoneticVariantDetector([a, b, c, d]).detect_canonical_pairs([])

    assert (pairs[0].source.lemma_1, pairs[0].target.lemma_1, pairs[0].rule) == (
        "akaṭa",
        "akata",
        "rule:t<->ṭ",
    )
