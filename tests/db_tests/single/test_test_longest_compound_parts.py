import json
from pathlib import Path
from types import SimpleNamespace
from typing import cast

from db.models import DpdHeadword
from db_tests.single.test_longest_compound_parts import (
    best_split,
    build_indexes,
    is_candidate,
    parse_line,
    save_exceptions,
)
from tools.paths import ProjectPaths

# rows copied from dpd.db, inflections cut to the forms the tests need
ROWS = [
    ("cātumāsa", "nt, comp", "catu > cātu + māsa + *a\ncatumāsa + *a", "cātumāsa"),
    ("paccayapavāraṇā", "fem, comp", "paccaya + pavāraṇā", "paccayapavāraṇā"),
    ("kumbhūpama", "adj, comp", "kumbha + upama", "kumbhūpama,kumbhūpamo"),
    ("tipiṭaka", "nt, comp", "ti + piṭaka", "tipiṭaka,tipiṭakaṃ"),
    ("kāṇamātar", "fem, comp", "kāṇa + mātar", "kāṇamātar,kāṇamātā,kāṇamātu"),
    ("gavassa", "nt, comp", "gava + assa", "gavassa,gavassaṃ"),
    ("gavāssa", "nt, comp", "gava + assa", "gavāssa,gavāssaṃ"),
    ("accāraddha", "adj, comp", "ati > aty > acc + āraddha", "accāraddha"),
    ("āraddhavīriya 1", "adj, comp", "āraddha + vīriya", "āraddhavīriya"),
    ("asīti 1.1", "card, fem sg, comp", "aṭṭha + dasa > asīti", "asīti"),
    ("ānāpānasati", "fem, abstr, comp", "ānāpāna + sati", "ānāpānasati"),
    ("ānāpānassati", "fem, abstr, comp", "ānāpāna + sati", "ānāpānassati"),
    ("udapānapanāḷī", "fem, comp", "udapāna + panāḷī", "udapānapanāḷī"),
]


def make_indexes() -> tuple[dict[str, set[str]], dict[tuple[str, ...], set[str]]]:
    words = [
        DpdHeadword(lemma_1=lemma, grammar=grammar, construction=cons, inflections=infl)
        for lemma, grammar, cons, infl in ROWS
    ]
    return build_indexes(words)


def test_parse_line_keeps_both_sides_of_arrow() -> None:
    parts = parse_line("ti > te + piṭaka [x] + *a")
    assert [(p.left, p.right) for p in parts] == [
        ("ti", "te"),
        ("piṭaka", "piṭaka"),
        ("*a", "*a"),
    ]
    assert parts[0].raw == "ti > te"


def test_joined_lemmas() -> None:
    form_index, parts_index = make_indexes()
    assert (
        best_split(
            "catu > cātu + māsa + paccaya + pavāraṇā",
            "cātumāsapaccayapavāraṇā",
            form_index,
            parts_index,
        )
        == "cātumāsa + paccayapavāraṇā"
    )


def test_sandhi_join_found_by_construction() -> None:
    form_index, parts_index = make_indexes()
    assert (
        best_split("aḍḍha + kumbha + upama", "aḍḍhakumbhūpama", form_index, parts_index)
        == "aḍḍha + kumbhūpama"
    )


def test_left_form_of_arrow_matches() -> None:
    form_index, parts_index = make_indexes()
    assert (
        best_split("ti > te + piṭaka + ika + x", "tepiṭakikax", form_index, parts_index)
        == "tipiṭaka + ika + x"
    )


def test_inflected_form_written_as_it_appears() -> None:
    form_index, parts_index = make_indexes()
    assert (
        best_split(
            "kāṇa + mātu + sikkhāpada", "kāṇamātusikkhāpada", form_index, parts_index
        )
        == "kāṇamātu + sikkhāpada"
    )


def test_spelling_variant_in_word_preferred() -> None:
    form_index, parts_index = make_indexes()
    assert (
        best_split("gava > gavā + assa + x", "gavāssax", form_index, parts_index)
        == "gavāssa + x"
    )


def test_no_hit_and_whole_line_ignored() -> None:
    form_index, parts_index = make_indexes()
    assert (
        best_split("dhamma + vinaya + x", "dhammavinayax", form_index, parts_index)
        is None
    )
    assert best_split("kumbha + upama", "kumbhūpama", form_index, parts_index) is None


def test_sound_change_part_absorbed_on_tie() -> None:
    form_index, parts_index = make_indexes()
    assert (
        best_split(
            "ati > aty > acc + āraddha + vīriya",
            "accāraddhavīriya",
            form_index,
            parts_index,
        )
        == "accāraddha + vīriya"
    )


def test_bracket_letter_is_not_a_longer_word() -> None:
    form_index, parts_index = make_indexes()
    assert (
        best_split("catu + [r] + asīti", "caturāsīti", form_index, parts_index) is None
    )


def test_bracket_letter_kept_next_to_merged_run() -> None:
    form_index, parts_index = make_indexes()
    assert (
        best_split(
            "udapāna + panāḷī + [y] + atthika",
            "udapānapanāḷiyatthika",
            form_index,
            parts_index,
        )
        == "udapānapanāḷī + [y] + atthika"
    )


def test_spelling_in_word_beats_joined_text() -> None:
    form_index, parts_index = make_indexes()
    assert (
        best_split(
            "ānāpāna + sati + samādhi", "ānāpānassatisamādhi", form_index, parts_index
        )
        == "ānāpānassati + samādhi"
    )


def test_is_candidate_needs_comp_no_root_and_construction() -> None:
    def hw(grammar: str, root_key: str, construction: str) -> DpdHeadword:
        return DpdHeadword(
            lemma_1="x", grammar=grammar, root_key=root_key, construction=construction
        )

    assert is_candidate(hw("nt, comp", "", "a + b"))
    assert not is_candidate(hw("nt, comp", "√gam", "a + b"))
    assert not is_candidate(hw("nt, comp", "", ""))
    assert not is_candidate(hw("sandhi, pr + ind", "", "asi + iti"))
    assert not is_candidate(hw("nt, compx", "", "a + b"))


def test_exceptions_saved_pali_sorted(tmp_path: Path) -> None:
    path = tmp_path / "exceptions.json"
    pth = cast(
        ProjectPaths, SimpleNamespace(longest_compound_parts_exceptions_path=path)
    )
    save_exceptions(pth, ["ṭhāna", "kāla", "akkanta"])
    assert json.loads(path.read_text(encoding="utf-8")) == ["akkanta", "kāla", "ṭhāna"]
    assert "ṭhāna" in path.read_text(encoding="utf-8")
