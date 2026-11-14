import json
import subprocess
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

import tools.docs_update_missing_words as mw
from db.models import Lookup
from tools.pali_text_files import cst_texts


def make_session(rows: list[Lookup]) -> Session:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Lookup.metadata.create_all(engine)
    session = Session(engine)
    session.add_all(rows)
    session.commit()
    return session


def make_finder(rows: list[Lookup] | None = None) -> Any:
    finder: Any = object.__new__(mw.MissingWordFinder)
    finder.db_session = make_session(rows or [])
    finder.has_data = mw.lookup_has_data()
    finder.all_inflections = set()
    finder.sandhi_ok_list = set()
    finder.variants = set()
    finder.spelling_mistakes = set()
    return finder


def test_classify_splits_the_missing_words() -> None:
    finder = make_finder(
        [
            Lookup(lookup_key="epdonly", epd="english"),
            Lookup(lookup_key="decononly", deconstructor='["a + b"]'),
            Lookup(lookup_key="abbrev", abbrev_other="an abbreviation"),
            Lookup(lookup_key="abbrevdecon", abbrev="x", deconstructor='["a + b"]'),
            Lookup(lookup_key="variantonly", variant='["main"]'),
            Lookup(lookup_key="hasheadword", headwords="[1]", deconstructor="a + b"),
        ]
    )

    unknown, needs = finder.classify_missing_words(
        [
            "absent",
            "epdonly",
            "decononly",
            "abbrev",
            "abbrevdecon",
            "variantonly",
            "hasheadword",
        ]
    )

    assert unknown == {"absent", "epdonly"}
    assert needs == {"decononly"}


def test_classify_reads_null_columns_as_empty() -> None:
    finder = make_finder([Lookup(lookup_key="nullrow", headwords=None, epd="epd")])

    unknown, needs = finder.classify_missing_words(["nullrow"])

    assert unknown == {"nullrow"}
    assert needs == set()


def test_classify_handles_more_words_than_one_chunk(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(mw, "CHUNK_SIZE", 2)
    finder = make_finder(
        [Lookup(lookup_key=f"decon{i}", deconstructor="a + b") for i in range(5)]
    )

    unknown, needs = finder.classify_missing_words(
        [f"decon{i}" for i in range(5)] + ["absent"]
    )

    assert unknown == {"absent"}
    assert needs == {f"decon{i}" for i in range(5)}


def test_is_missing_skips_every_known_source() -> None:
    finder = make_finder()
    finder.all_inflections = {"inflected"}
    finder.sandhi_ok_list = {"sandhiok"}
    finder.variants = {"variant"}
    finder.spelling_mistakes = {"mistake"}

    for word in ["inflected", "sandhiok", "variant", "mistake"]:
        assert not finder.is_missing(word)
    assert finder.is_missing("other")


def test_count_book_lists_the_most_frequent_missing_words_first(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    text = ["known"] + ["rare"] + ["common"] * 3 + ["middle"] * 2 + ["abbrev"] * 9
    monkeypatch.setattr(mw, "make_cst_text_list", lambda *a, **k: text)
    finder = make_finder(
        [
            Lookup(lookup_key="abbrev", abbrev_other="an abbreviation"),
            Lookup(lookup_key="middle", deconstructor="a + b"),
        ]
    )
    finder.all_inflections = {"known"}

    words, unknown, needs, top = finder.count_book(CST_ONLY)

    assert (words, unknown, needs) == (5, 2, 1)
    assert top == [("common", 3), ("middle", 2), ("rare", 1)]


def test_missing_percent() -> None:
    assert mw.missing_percent(1000, 10, 15) == "2.5%"
    assert mw.missing_percent(0, 0, 0) == ""


CST_ONLY = mw.Book("Book", ["kn1"], [])

ROWS = [
    ("Pārājika", 100, 0, 0, []),
    ("Pācittiya", 200, 1, 3, [("kaṭūpago", 4), ("gīvūpago", 2)]),
    (mw.TOTAL_LABEL, 300, 1, 3, []),
]


def test_markdown_has_one_title_and_the_date_first() -> None:
    text = mw.render_markdown("2026-11-11", [("Vinaya", ROWS)])

    lines = text.splitlines()
    assert lines[0] == "# Missing Words in DPD"
    assert "**Date: 2026-11-11**" in lines[:6]
    assert [line for line in lines if line.startswith("# ")] == [lines[0]]


def test_markdown_wraps_the_page_for_full_width_tables() -> None:
    text = mw.render_markdown("2026-11-11", [("Vinaya", ROWS)])

    assert '<div class="missing-words" markdown>' in text
    assert text.rstrip().endswith("</div>")


def test_markdown_table_and_percent_column() -> None:
    text = mw.render_markdown("2026-11-11", [("Vinaya", ROWS)])

    assert (
        "| Book | Distinct words | Unrecognised | Needs a headword | Missing % |"
        in text
    )
    assert "| Pācittiya | 200 | 1 | 3 | 2.0% |" in text
    assert "| **All books added** | **300** | **1** | **3** | **1.3%** |" in text


def test_markdown_top_words_per_book() -> None:
    text = mw.render_markdown("2026-11-11", [("Vinaya", ROWS)])
    top = text[text.index("## Most frequent missing words") :]

    assert "**Pārājika**\n\nNo missing words." in top
    assert "**Pācittiya**\n\n1. kaṭūpago (4)\n2. gīvūpago (2)" in top
    assert mw.TOTAL_LABEL not in top
    # a book is a bold line, so it stays out of the table of contents
    assert "#### " not in top


def test_typst_escapes_its_markup_characters() -> None:
    assert mw.typst_escape("a#b*c_d") == "a\\#b\\*c\\_d"


def test_typst_has_the_date_and_the_top_words() -> None:
    text = mw.render_typst("2026-11-11", [("Vinaya", ROWS)])

    assert "*Date: 2026-11-11*" in text
    assert "+ kaṭūpago (4)" in text


def test_markdown_invites_contributions_with_a_live_link_at_the_top() -> None:
    text = mw.render_markdown("2026-11-11", [("Vinaya", ROWS)])

    sentence = text.splitlines()[2]
    assert sentence.startswith("If you would like to contribute to the dictionary")
    assert f"[contribution form]({mw.CONTRIBUTE_FORM_URL})" in sentence


def test_typst_invites_contributions_with_a_live_link_at_the_top() -> None:
    text = mw.render_typst("2026-11-11", [("Vinaya", ROWS)])

    sentence = next(
        line for line in text.splitlines() if line.startswith("If you would like")
    )
    assert f'#link("{mw.CONTRIBUTE_FORM_URL}")[contribution form]' in sentence
    assert text.index(sentence) < text.index("*Date: 2026-11-11*")


def test_importing_the_tool_leaves_the_shared_book_list_alone() -> None:
    assert not set(mw.SPLIT_COMMENTARY_FILES) & set(cst_texts)


def test_equal_counts_are_listed_in_paali_order(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    text = ["ṭ1", "c1", "a1", "b1", "z"] + ["z"] * 4 + ["d1"]
    monkeypatch.setattr(mw, "make_cst_text_list", lambda *_a, **_k: text)
    finder = make_finder()

    *_, top = finder.count_book(CST_ONLY)

    # Pāḷi order puts ṭ before d and b. Plain Unicode order would put it last.
    assert [word for word, _ in top] == ["z", "a1", "c1", "ṭ1", "d1"]


def sc_source(
    words: dict[str, int], folders: dict[str, list[str]] | None = None
) -> SimpleNamespace:
    """A fake SuttaCentral book. `folders` maps each folder to its files."""
    folders = folders if folders is not None else {"folder": ["file"]}
    return SimpleNamespace(
        pali_file_list=[f for files in folders.values() for f in files],
        pali_paths=list(folders),
        make_file_list=lambda folder: folders[folder],
        word_dict={word: [object()] * count for word, count in words.items()},
    )


def test_words_only_suttacentral_has_are_counted_with_the_cst_words(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        mw, "make_cst_text_list", lambda *_a, **_k: ["shared"] * 2 + ["cstonly"]
    )
    monkeypatch.setattr(
        mw,
        "sutta_central_books",
        {"one": sc_source({"shared": 7, "sconly": 5}), "two": sc_source({"sconly": 1})},
    )
    finder = make_finder([Lookup(lookup_key="sconly", deconstructor="a + b")])

    words, unknown, needs, top = finder.count_book(
        mw.Book("Row", ["kn1"], ["one", "two"])
    )

    assert words == 3
    assert (unknown, needs) == (2, 1)
    # a word in both texts keeps its CST count, so the texts are not added
    assert top == [("sconly", 6), ("shared", 2), ("cstonly", 1)]


def test_a_missing_suttacentral_folder_stops_the_count(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(mw, "make_cst_text_list", lambda *_a, **_k: ["word"])
    monkeypatch.setattr(
        mw,
        "sutta_central_books",
        {"one": sc_source({}, {"folder": []})},
    )
    finder = make_finder()

    with pytest.raises(FileNotFoundError, match="one"):
        finder.count_book(mw.Book("Row", ["kn1"], ["one"]))


def test_one_missing_folder_of_two_stops_the_count(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(mw, "make_cst_text_list", lambda *_a, **_k: ["word"])
    monkeypatch.setattr(
        mw,
        "sutta_central_books",
        {"ap": sc_source({"w": 1}, {"tha-ap": ["file"], "thi-ap": []})},
    )
    finder = make_finder()

    with pytest.raises(FileNotFoundError, match="ap"):
        finder.count_book(mw.Book("Row", ["kn10", "kn11"], ["ap"]))


def test_a_row_with_a_story_range_counts_only_those_cst_stories(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    asked: list[range] = []

    def jataka_words(story_range: range, **_k: Any) -> list[str]:
        asked.append(story_range)
        return ["storyword"] * 3

    monkeypatch.setattr(mw, "make_cst_jataka_text_list", jataka_words)
    monkeypatch.setattr(
        mw, "make_cst_text_list", lambda *_a, **_k: pytest.fail("whole book read")
    )
    monkeypatch.setattr(mw, "sutta_central_books", {"part": sc_source({"other": 1})})
    finder = make_finder()

    words, unknown, _needs, top = finder.count_book(
        mw.Book("Row", ["kn14"], ["part"], range(1, 11))
    )

    assert asked == [range(1, 11)]
    assert words == 2
    assert (unknown, top[0]) == (2, ("storyword", 3))


def test_the_jataka_rows_cover_every_story_once() -> None:
    stories = [
        number for book in mw.JATAKA_ROOT for number in (book.story_range or range(0))
    ]

    assert sorted(stories) == list(range(1, 548))
    assert len(mw.JATAKA_ROOT) == 5
    assert all(book.cst_codes == ["kn14"] for book in mw.JATAKA_ROOT)


def test_every_suttacentral_book_named_in_a_table_exists() -> None:
    from gui2.books import sutta_central_books

    for _title, books in mw.TABLES:
        for book in books:
            for sc_book in book.sc_books:
                assert sc_book in sutta_central_books, book.name


def test_every_cst_code_named_in_a_table_exists() -> None:
    known = set(cst_texts) | set(mw.SPLIT_COMMENTARY_FILES)
    for _title, books in mw.TABLES:
        for book in books:
            assert set(book.cst_codes) <= known, book.name


def test_every_suttacentral_row_holds_the_cst_books_of_its_suttacentral_books() -> None:
    from gui2.books import sutta_central_books

    for _title, books in mw.TABLES:
        for book in books:
            if book.sc_books:
                held = {
                    code
                    for sc_book in book.sc_books
                    for code in sutta_central_books[sc_book].cst_books
                }
                assert held == set(book.cst_codes), book.name


class FakePaths:
    def __init__(self, folder) -> None:
        self.docs_missing_words_md_path = folder / "missing_words.md"
        self.docs_missing_words_pdf_path = folder / "missing_words.pdf"


class FakeFinder:
    def __init__(self, _pth) -> None:
        pass

    def count_book(self, _book):
        return 10, 1, 2, [("word", 3)]


def run_main(monkeypatch: pytest.MonkeyPatch, tmp_path, typst) -> FakePaths:
    paths = FakePaths(tmp_path)
    monkeypatch.setattr(mw, "ProjectPaths", lambda: paths)
    monkeypatch.setattr(mw, "MissingWordFinder", FakeFinder)
    monkeypatch.setattr(mw, "TABLES", [("Vinaya", [mw.Book("Row", ["vin5"], [])])])
    monkeypatch.setattr(mw.subprocess, "run", typst)
    mw.main()
    return paths


def test_main_writes_the_page_and_the_pdf(
    monkeypatch: pytest.MonkeyPatch, tmp_path
) -> None:
    def typst(cmd, input, check):
        Path(cmd[-1]).write_bytes(b"%PDF new")

    paths = run_main(monkeypatch, tmp_path, typst)

    assert paths.docs_missing_words_pdf_path.read_bytes() == b"%PDF new"
    assert paths.docs_missing_words_md_path.read_text().startswith(
        "# Missing Words in DPD"
    )


def test_a_failed_pdf_leaves_the_page_and_the_pdf_as_they_were(
    monkeypatch: pytest.MonkeyPatch, tmp_path
) -> None:
    (tmp_path / "missing_words.md").write_text("old page")
    (tmp_path / "missing_words.pdf").write_bytes(b"old pdf")

    def typst(cmd, input, check):
        raise subprocess.CalledProcessError(1, cmd)

    with pytest.raises(subprocess.CalledProcessError):
        run_main(monkeypatch, tmp_path, typst)

    assert (tmp_path / "missing_words.md").read_text() == "old page"
    assert (tmp_path / "missing_words.pdf").read_bytes() == b"old pdf"


def test_saved_pass1_auto_words_still_count_as_missing(
    monkeypatch: pytest.MonkeyPatch, tmp_path
) -> None:
    """The report reflects the database, so Pass1 Auto drafts are not subtracted."""
    data_dir = tmp_path / "gui2" / "data"
    data_dir.mkdir(parents=True)
    (data_dir / "pass1_auto_ap.json").write_text(json.dumps({"w1": {}}))
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(mw, "make_cst_text_list", lambda *_a, **_k: ["w1"])
    monkeypatch.setattr(
        mw, "sutta_central_books", {"ap": SimpleNamespace(cst_books=["kn10"])}
    )
    finder = make_finder()

    words, unknown, needs, _top = finder.count_book(mw.Book("Row", ["kn10"], []))

    assert (words, unknown, needs) == (1, 1, 0)


HIGHLIGHT_ROWS = [
    ("Quiet", 100, mw.HIGHLIGHT_UNRECOGNISED - 1, 3, []),
    ("Busy", 200, mw.HIGHLIGHT_UNRECOGNISED, 3, []),
    (mw.TOTAL_LABEL, 300, 500, 6, []),
]


def test_markdown_highlights_a_book_at_the_limit() -> None:
    text = mw.render_markdown("2026-11-11", [("Vinaya", HIGHLIGHT_ROWS)])

    assert mw.HIGHLIGHT_NOTE in text
    assert "| Quiet | 100 | 19 | 3 | 22.0% |" in text
    assert "| Busy | 200 | <mark>20</mark> | 3 | 11.5% |" in text
    assert "| **All books added** | **300** | **500** | **6** | **168.7%** |" in text


def test_typst_highlights_a_book_at_the_limit() -> None:
    text = mw.render_typst("2026-11-11", [("Vinaya", HIGHLIGHT_ROWS)])

    fill = f'table.cell(fill: rgb("{mw.HIGHLIGHT_COLOUR}"))'
    assert "[Quiet], [100], [19], [3]" in text
    assert f"[Busy], [200], {fill}[20], [3]" in text
    assert f"{fill}[*500*]" not in text
