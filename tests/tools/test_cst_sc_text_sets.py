from pathlib import Path
from types import SimpleNamespace

import pytest

import tools.cst_sc_text_sets as sets

# Real shapes: the first story heading is plain, later ones carry "(2-1-1)".
FIRST = """jātakapāḷi
1. apaṇṇakajātakaṃ
alpaṃ bhikkhu
151. rājovādajātakaṃ (2-1-1)
bettaṃ gamma
"""
# The second file starts in the middle of story 151, with no heading.
SECOND = """delta epsilon
152. dutiyajātakaṃ
zeta
999. a heading of another shape
eta
"""


@pytest.fixture
def jataka_files(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    (tmp_path / "one.txt").write_text(FIRST, encoding="utf-8")
    (tmp_path / "two.txt").write_text(SECOND, encoding="utf-8")
    monkeypatch.setattr(sets, "pth", SimpleNamespace(cst_txt_dir=tmp_path))
    monkeypatch.setitem(sets.cst_texts, "kn14", ["one.txt", "two.txt"])


def words(story_range: range) -> list[str]:
    return sets.make_cst_jataka_text_list(story_range, dedupe=False, show_errors=False)


def test_a_story_runs_from_its_heading_to_the_next_one(jataka_files: None) -> None:
    assert words(range(151, 152)) == [
        "rājovādajātakaṃ",
        "bettaṃ",
        "gamma",
        "delta",
        "epsilon",
    ]


def test_a_second_file_continues_the_story_the_first_file_ended_on(
    jataka_files: None,
) -> None:
    # "delta epsilon" opens the second file before any heading: it is story 151
    assert "delta" in words(range(151, 152))
    assert "delta" not in words(range(1, 2))


def test_the_lines_before_the_first_heading_count_with_story_one(
    jataka_files: None,
) -> None:
    assert words(range(1, 2)) == [
        "jātakapāḷi",
        "apaṇṇakajātakaṃ",
        "alpaṃ",
        "bhikkhu",
    ]


def test_a_heading_with_another_shape_stays_with_the_story_before_it(
    jataka_files: None,
) -> None:
    assert "eta" in words(range(152, 153))
    assert words(range(999, 1000)) == []


def test_ranges_that_cover_every_story_hold_every_word_once(
    jataka_files: None,
) -> None:
    whole = sets.make_cst_text_list(["kn14"], dedupe=False, show_errors=False)
    parts = words(range(1, 100)) + words(range(100, 1000))

    assert sorted(parts) == sorted(whole)


HYPHEN_TEXT = "dhamma-cakkaṃ pavattitaṃ (bracket) dhamma\nsaṅgho-dhamma dhamma-cakkaṃ\n"
# Expected lists taken from the function as it was before the cleaning and the
# hyphen and dedupe steps moved into helpers.
HYPHEN_CASES = [
    (
        True,
        True,
        ["dhammacakkaṃ", "dhamma", "cakkaṃ", "pavattitaṃ", "saṅghodhamma", "saṅgho"],
    ),
    (True, False, ["dhammacakkaṃ", "pavattitaṃ", "dhamma", "saṅghodhamma"]),
    (
        False,
        True,
        [
            "dhammacakkaṃ",
            "dhamma",
            "cakkaṃ",
            "pavattitaṃ",
            "dhamma",
            "saṅghodhamma",
            "saṅgho",
            "dhamma",
            "dhammacakkaṃ",
            "dhamma",
            "cakkaṃ",
        ],
    ),
    (
        False,
        False,
        ["dhammacakkaṃ", "pavattitaṃ", "dhamma", "saṅghodhamma", "dhammacakkaṃ"],
    ),
]


@pytest.mark.parametrize(("dedupe", "hyphenated", "expected"), HYPHEN_CASES)
def test_make_cst_text_list_keeps_its_exact_output(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    dedupe: bool,
    hyphenated: bool,
    expected: list[str],
) -> None:
    (tmp_path / "a.txt").write_text(HYPHEN_TEXT, encoding="utf-8")
    monkeypatch.setattr(sets, "pth", SimpleNamespace(cst_txt_dir=tmp_path))
    monkeypatch.setitem(sets.cst_texts, "tmpbook", ["a.txt"])

    assert (
        sets.make_cst_text_list(
            ["tmpbook"],
            dedupe=dedupe,
            add_hyphenated_parts=hyphenated,
            show_errors=False,
        )
        == expected
    )
