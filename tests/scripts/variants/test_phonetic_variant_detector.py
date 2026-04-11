"""Tests for ``scripts/variants/phonetic_variant_detector.py`` (issue #144 part 1)."""

from types import SimpleNamespace

from scripts.variants.phonetic_variant_detector import (
    PhoneticVariantCandidate,
    PhoneticVariantDetector,
)


def make_headword(
    lemma_1: str,
    lemma_clean: str | None = None,
    pos: str = "verb",
    construction_clean: str = "",
    family_word: str = "",
    family_root: str = "",
    root_key: str = "",
    meaning_combo: str = "",
    var_phonetic: str = "",
    var_text: str = "",
    variant: str = "",
) -> SimpleNamespace:
    return SimpleNamespace(
        lemma_1=lemma_1,
        lemma_clean=lemma_clean if lemma_clean is not None else lemma_1,
        pos=pos,
        construction_clean=construction_clean,
        family_word=family_word,
        family_root=family_root,
        root_key=root_key,
        meaning_combo=meaning_combo,
        var_phonetic=var_phonetic,
        var_text=var_text,
        variant=variant,
    )


def _rules_of(candidates: list[PhoneticVariantCandidate]) -> set[str]:
    return {c.rule for c in candidates}


def _pairs_of(
    candidates: list[PhoneticVariantCandidate],
) -> set[tuple[str, str]]:
    return {(c.lemma_1, c.candidate_lemma_clean) for c in candidates}


def test_same_construction_groups_pairs() -> None:
    a = make_headword("jeti", construction_clean="ji + *a", pos="verb")
    b = make_headword("jayati", construction_clean="ji + *a", pos="verb")
    lonely = make_headword("gacchati", construction_clean="gam + *a", pos="verb")

    detector = PhoneticVariantDetector([a, b, lonely])
    candidates = detector.detect_same_construction()

    assert all(c.rule == "same_construction" for c in candidates)
    assert ("jeti", "jayati") in _pairs_of(candidates)
    assert ("jayati", "jeti") in _pairs_of(candidates)
    assert all(
        "gacchati" not in (c.lemma_1, c.candidate_lemma_clean) for c in candidates
    )


def test_same_construction_ignores_empty_construction() -> None:
    a = make_headword("foo", construction_clean="", pos="noun")
    b = make_headword("bar", construction_clean="", pos="noun")

    detector = PhoneticVariantDetector([a, b])
    assert detector.detect_same_construction() == []


def test_rule_e_aya_matches_known_pair() -> None:
    jayati = make_headword("jayati")
    jeti = make_headword("jeti")

    detector = PhoneticVariantDetector([jayati, jeti])
    candidates = detector.detect_by_rules()

    assert "rule:e<->aya" in _rules_of(candidates)
    assert ("jayati", "jeti") in _pairs_of(candidates)
    assert ("jeti", "jayati") in _pairs_of(candidates)


def test_rule_niggahita_velar_matches_known_pair() -> None:
    a = make_headword("akathaṃkathī")
    b = make_headword("akathaṅkathī")

    detector = PhoneticVariantDetector([a, b])
    candidates = detector.detect_by_rules()

    assert "rule:ṃ<->ṅ" in _rules_of(candidates)
    assert ("akathaṃkathī", "akathaṅkathī") in _pairs_of(candidates)


def test_rule_t_retroflex_matches_known_pair() -> None:
    a = make_headword("akaṭa")
    b = make_headword("akata")

    detector = PhoneticVariantDetector([a, b])
    candidates = detector.detect_by_rules()

    assert "rule:t<->ṭ" in _rules_of(candidates)
    assert ("akaṭa", "akata") in _pairs_of(candidates)


def test_skips_candidate_already_in_var_phonetic() -> None:
    """If the editor has already recorded the candidate, don't re-surface it.

    Covers all three detectors: same_construction, rules, and levenshtein.
    """
    # same_construction path
    sc_a = make_headword(
        "jayati",
        construction_clean="ji + *a",
        pos="verb",
        var_phonetic="jeti",
    )
    sc_b = make_headword("jeti", construction_clean="ji + *a", pos="verb")

    # rule path (different dataset to keep assertions narrow)
    rule_a = make_headword("akaṭa", var_phonetic="akata")
    rule_b = make_headword("akata")

    # levenshtein path
    lev_a = make_headword(
        "kariyati",
        pos="verb",
        family_word="karoti",
        var_phonetic="karīyati",
    )
    lev_b = make_headword("karīyati", pos="verb", family_word="karoti")

    detector = PhoneticVariantDetector([sc_a, sc_b, rule_a, rule_b, lev_a, lev_b])

    sc_candidates = [
        c for c in detector.detect_same_construction() if c.lemma_1 == "jayati"
    ]
    assert sc_candidates == []

    rule_candidates = [c for c in detector.detect_by_rules() if c.lemma_1 == "akaṭa"]
    assert rule_candidates == []

    lev_candidates = [
        c for c in detector.detect_by_levenshtein() if c.lemma_1 == "kariyati"
    ]
    assert lev_candidates == []

    # Sanity: the reverse direction (where var_phonetic is empty) still fires.
    assert any(
        c.lemma_1 == "jeti" and c.candidate_lemma_clean == "jayati"
        for c in detector.detect_same_construction()
    )


def test_candidate_is_lemma_clean_and_dedupes_target_homonyms() -> None:
    """Two target homonyms sharing lemma_clean should collapse to one row.

    The source 'akaṭa' matches both 'akata 1' and 'akata 2' (same lemma_clean)
    via rule t<->ṭ. Candidates key on lemma_clean, so only one row is emitted.
    """
    source = make_headword("akaṭa", lemma_clean="akaṭa")
    target_1 = make_headword("akata 1", lemma_clean="akata")
    target_2 = make_headword("akata 2", lemma_clean="akata")

    detector = PhoneticVariantDetector([source, target_1, target_2])
    candidates = [c for c in detector.detect_by_rules() if c.lemma_1 == "akaṭa"]

    assert len(candidates) == 1
    assert candidates[0].candidate_lemma_clean == "akata"
    assert candidates[0].rule == "rule:t<->ṭ"


def test_levenshtein_within_family() -> None:
    a = make_headword("karīyati", pos="verb", family_word="karoti")
    b = make_headword("kariyati", pos="verb", family_word="karoti")

    detector = PhoneticVariantDetector([a, b])
    candidates = detector.detect_by_levenshtein()

    pairs = _pairs_of(candidates)
    assert ("karīyati", "kariyati") in pairs
    assert ("kariyati", "karīyati") in pairs
    assert any(c.rule.startswith("levenshtein:") for c in candidates)


def test_levenshtein_ignores_different_first_char() -> None:
    a = make_headword("kariyati", pos="verb", family_word="karoti")
    b = make_headword("mariyati", pos="verb", family_word="karoti")

    detector = PhoneticVariantDetector([a, b])
    assert detector.detect_by_levenshtein() == []


def test_levenshtein_ignores_different_family() -> None:
    a = make_headword("kariyati", pos="verb", family_word="karoti")
    b = make_headword("kariyati2", pos="verb", family_word="some_other_family")

    detector = PhoneticVariantDetector([a, b])
    assert detector.detect_by_levenshtein() == []


def test_levenshtein_ignores_different_pos() -> None:
    """pos mismatch filter — without this, a full-db run produced ~200k false positives."""
    a = make_headword("kariyati", pos="verb", family_word="karoti")
    b = make_headword("kariyāti", pos="noun", family_word="karoti")

    detector = PhoneticVariantDetector([a, b])
    assert detector.detect_by_levenshtein() == []


def test_detect_canonical_pairs_collapses_symmetric_duplicates() -> None:
    """Each unordered lemma_clean pair appears at most once per rule."""
    jayati = make_headword(
        "jayati", construction_clean="ji + *a", pos="verb", family_word="ji"
    )
    jeti = make_headword(
        "jeti", construction_clean="ji + *a", pos="verb", family_word="ji"
    )

    detector = PhoneticVariantDetector([jayati, jeti])
    pairs = detector.detect_canonical_pairs()

    same_construction = [p for p in pairs if p.rule == "same_construction"]
    e_aya = [p for p in pairs if p.rule == "rule:e<->aya"]

    assert len(same_construction) == 1
    assert len(e_aya) == 1


def test_detect_canonical_pairs_filters_if_either_side_recorded() -> None:
    """If either side already records the other, drop the whole pair."""
    jayati = make_headword(
        "jayati",
        construction_clean="ji + *a",
        pos="verb",
        var_phonetic="jeti",
    )
    jeti = make_headword("jeti", construction_clean="ji + *a", pos="verb")

    detector = PhoneticVariantDetector([jayati, jeti])
    pairs = detector.detect_canonical_pairs()

    assert pairs == []


def test_detect_canonical_pairs_includes_homonyms_in_targets() -> None:
    """Homonyms sharing lemma_clean all appear in the targets list."""
    source = make_headword("akaṭa", lemma_clean="akaṭa")
    target_1 = make_headword("akata 1", lemma_clean="akata")
    target_2 = make_headword("akata 2", lemma_clean="akata")

    detector = PhoneticVariantDetector([source, target_1, target_2])
    pairs = [p for p in detector.detect_canonical_pairs() if p.rule == "rule:t<->ṭ"]

    assert len(pairs) == 1
    target_lemmas = {t.lemma_1 for t in pairs[0].targets}
    assert target_lemmas == {"akata 1", "akata 2"}


def test_detect_canonical_pairs_filters_targets_to_same_root_family_and_key() -> None:
    source = make_headword("seti", family_root="sayati", root_key="si")
    right = make_headword(
        "sayati 1", lemma_clean="sayati", family_root="sayati", root_key="si"
    )
    wrong_root = make_headword(
        "sayati 2",
        lemma_clean="sayati",
        family_root="sayati",
        root_key="as",
    )
    wrong_family = make_headword(
        "sayati 3",
        lemma_clean="sayati",
        family_root="sasati",
        root_key="si",
    )

    detector = PhoneticVariantDetector([source, right, wrong_root, wrong_family])
    pairs = [p for p in detector.detect_canonical_pairs() if p.rule == "rule:e<->aya"]

    assert len(pairs) == 1
    target_lemmas = {t.lemma_1 for t in pairs[0].targets}
    assert target_lemmas == {"sayati 1"}


def test_detect_canonical_pairs_filters_targets_to_same_word_family() -> None:
    source = make_headword("jeti", family_word="ji")
    right = make_headword("jayati 1", lemma_clean="jayati", family_word="ji")
    wrong = make_headword("jayati 2", lemma_clean="jayati", family_word="janeti")

    detector = PhoneticVariantDetector([source, right, wrong])
    pairs = [p for p in detector.detect_canonical_pairs() if p.rule == "rule:e<->aya"]

    assert len(pairs) == 1
    target_lemmas = {t.lemma_1 for t in pairs[0].targets}
    assert target_lemmas == {"jayati 1"}


def test_detect_canonical_pairs_sorted_by_rule_and_lemma_1() -> None:
    """Pairs are ordered by (rule, source.lemma_1)."""
    jayati = make_headword(
        "jayati", construction_clean="ji + *a", pos="verb", family_word="ji"
    )
    jeti = make_headword(
        "jeti", construction_clean="ji + *a", pos="verb", family_word="ji"
    )
    akata = make_headword("akata")
    akaṭa = make_headword("akaṭa")

    detector = PhoneticVariantDetector([jayati, jeti, akata, akaṭa])
    pairs = detector.detect_canonical_pairs()

    keys = [(p.rule, p.source.lemma_1) for p in pairs]
    assert keys == sorted(keys)


def test_detect_all_returns_candidates_from_enabled_methods() -> None:
    jayati = make_headword(
        "jayati",
        construction_clean="ji + *a",
        pos="verb",
        family_word="ji",
    )
    jeti = make_headword(
        "jeti",
        construction_clean="ji + *a",
        pos="verb",
        family_word="ji",
    )
    kariyati = make_headword("kariyati", family_word="karoti")
    karīyati = make_headword("karīyati", family_word="karoti")

    detector = PhoneticVariantDetector([jayati, jeti, kariyati, karīyati])
    all_candidates = detector.detect_all()
    rules = _rules_of(all_candidates)

    assert "same_construction" in rules
    assert any(r.startswith("rule:") for r in rules)
    assert not any(r.startswith("levenshtein:") for r in rules)
