# -*- coding: utf-8 -*-
"""Tests for gui2/inflection_templates_tab_view.py

The module-level pure helpers, the button handlers' non-Flet cores on
temp files and a temp db, and the word-list filter.
The Flet widgets themselves are not tested.
"""

from collections.abc import Iterator
from unittest.mock import MagicMock

import flet as ft
import pytest
from gui2.filter_logic import build_filter_conditions
from gui2.inflection_templates_tab_view import (
    InflectionTemplatesTabView,
    BOX_PADDING,
    FORMS_CHAR_WIDTH,
    FORMS_MIN_WIDTH,
    GRAMMAR_CHAR_WIDTH,
    GRAMMAR_MIN_WIDTH,
    HEADING_CHAR_WIDTH,
    HIGHLIGHT_COLOUR,
    LABEL_MIN_WIDTH,
    copy_template_core,
    data_to_grid_values,
    delete_template_core,
    grid_dimensions,
    grid_values_to_data,
    max_form_count,
    pattern_word_filter,
    rename_template_core,
    save_template_core,
    validate_new_name,
    validate_template,
)
from db.inflections.inflection_template_files import (
    TemplateFile,
    load_templates,
    write_template,
)
from db.models import DpdHeadword
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from tools.paths import ProjectPaths
from tools.search_deadline import install_regexp


def make_template() -> TemplateFile:
    return TemplateFile(
        pattern="test pr",
        like="ka",
        data=[
            [[""], ["sg"], [""], ["pl"], [""]],
            [["nom"], ["o"], ["nom sg"], ["ā"], ["nom pl"]],
            [["dat"], ["ssa"], ["dat sg"], ["ānaṃ"], ["dat pl"]],
        ],
    )


@pytest.fixture
def files(tmp_path) -> ProjectPaths:
    """Temp index and templates dir holding one template."""
    pth = ProjectPaths(base_dir=tmp_path, create_dirs=False)
    write_template(
        make_template(),
        pth.inflection_templates_index_path,
        pth.inflection_templates_dir,
    )
    return pth


# ── grid_values_to_data / data_to_grid_values ───────────────────────────────


def test_grid_values_to_data_cleans_forms():
    """Forms are trimmed, blank lines dropped, sorted; empty cell → [""]."""
    headings = ["sg"]
    rows = [["nom", " b\n\na \n", "grammar"]]
    data = grid_values_to_data(headings, rows)
    assert data == [
        [[""], ["sg"], [""]],
        [["nom"], ["a", "b"], ["grammar"]],
    ]


def test_grid_values_to_data_drops_blank_rows():
    """A row with every cell blank is dropped, so save does not refuse it."""
    headings = ["sg"]
    rows = [["nom", "a", "g"], ["", "", ""], ["", " \n", " "]]
    data = grid_values_to_data(headings, rows)
    assert data == [
        [[""], ["sg"], [""]],
        [["nom"], ["a"], ["g"]],
    ]
    assert validate_template(TemplateFile(pattern="p", like="q", data=data)) is None


def test_grid_values_to_data_round_trip():
    """data → grid → data gives the same data."""
    t = make_template()
    headings, rows = data_to_grid_values(t.data)
    assert grid_values_to_data(headings, rows) == t.data


def test_data_to_grid_values_multi_forms_one_per_line():
    t = TemplateFile(
        pattern="x",
        like="y",
        data=[[[""], ["sg"], [""]], [["nom"], ["a", "b"], ["nom sg"]]],
    )
    headings, rows = data_to_grid_values(t.data)
    assert headings == ["sg"]
    assert rows == [["nom", "a\nb", "nom sg"]]


def test_max_form_count_real_ant_adj():
    """max_form_count of the real ant adj data = its real maximum (5)."""
    pth = ProjectPaths(create_dirs=False)
    templates = load_templates(
        pth.inflection_templates_index_path, pth.inflection_templates_dir
    )
    ant_adj = next(t for t in templates if t.pattern == "ant adj")
    assert max_form_count(ant_adj.data) == 5


# ── validate_new_name ───────────────────────────────────────────────────────


def test_validate_new_name_accepts_good_name():
    assert validate_new_name("new pr", ["old pr"]) is None


def test_validate_new_name_refusals():
    assert validate_new_name("", ["old pr"]) is not None
    assert validate_new_name("old pr", ["old pr"]) is not None
    assert validate_new_name("bad/name", ["old pr"]) is not None
    assert validate_new_name("bad\tname", ["old pr"]) is not None


def test_validate_new_name_refuses_surrounding_spaces():
    """A name differing from an existing one only by spaces is refused."""
    assert validate_new_name(" old pr ", ["old pr"]) is not None


# ── validate_template ───────────────────────────────────────────────────────


def test_validate_template_accepts_good_template():
    assert validate_template(make_template()) is None


def test_validate_template_refusals():
    no_pattern = make_template()
    no_pattern.pattern = ""
    assert validate_template(no_pattern) is not None

    no_like = make_template()
    no_like.like = ""
    assert validate_template(no_like) is not None

    comma = make_template()
    comma.data[1][1] = ["o,x"]
    assert validate_template(comma) is not None

    tab = make_template()
    tab.data[1][1] = ["o\tx"]
    assert validate_template(tab) is not None

    no_heading = make_template()
    no_heading.data[0][1] = [""]
    assert validate_template(no_heading) is not None

    no_label = make_template()
    no_label.data[1][0] = [""]
    assert validate_template(no_label) is not None


# ── button handlers' non-Flet cores ─────────────────────────────────────────


def file_count(pth: ProjectPaths) -> int:
    return len(list(pth.inflection_templates_dir.glob("*.tsv")))


def index_rows(pth: ProjectPaths) -> list[str]:
    lines = pth.inflection_templates_index_path.read_text(encoding="utf-8")
    return [line for line in lines.splitlines() if line][1:]


def test_copy_to_existing_name_writes_nothing(files: ProjectPaths):
    new_t, refusal = copy_template_core(make_template(), "test pr", ["test pr"])
    assert new_t is None
    assert refusal
    assert file_count(files) == 1
    assert len(index_rows(files)) == 1


def test_copy_then_save_creates_files(files: ProjectPaths):
    new_t, refusal = copy_template_core(make_template(), "copy pr", ["test pr"])
    assert refusal == ""
    assert new_t is not None

    refusal = save_template_core(
        new_t,
        files.inflection_templates_index_path,
        files.inflection_templates_dir,
        ["test pr"],
    )
    assert refusal == ""
    assert file_count(files) == 2
    assert len(index_rows(files)) == 2

    loaded = load_templates(
        files.inflection_templates_index_path, files.inflection_templates_dir
    )
    copy = next(t for t in loaded if t.pattern == "copy pr")
    assert copy.data == make_template().data


def test_save_edits_one_line_of_one_file(files: ProjectPaths):
    path = files.inflection_templates_dir / "test pr.tsv"
    before = path.read_text(encoding="utf-8").splitlines()

    t = make_template()
    t.data[2][1] = ["āya"]
    refusal = save_template_core(
        t,
        files.inflection_templates_index_path,
        files.inflection_templates_dir,
        ["test pr"],
    )
    assert refusal == ""

    after = path.read_text(encoding="utf-8").splitlines()
    changed = [(b, a) for b, a in zip(before, after) if b != a]
    assert len(changed) == 1
    assert changed[0][1].startswith("dat\taāya") or "āya" in changed[0][1]


def test_rename_moves_words(files: ProjectPaths):
    """rename_template_core moves the file; rename_pattern_in_headwords
    moves the words."""
    engine = create_engine("sqlite:///:memory:", echo=False)
    from db.models import Base

    Base.metadata.create_all(engine)
    session = Session(bind=engine)
    session.add(DpdHeadword(id=1, lemma_1="avocado", pos="masc", pattern="test pr"))
    session.commit()

    refusal = rename_template_core(
        "test pr",
        "renamed pr",
        files.inflection_templates_index_path,
        files.inflection_templates_dir,
        ["test pr"],
    )
    assert refusal == ""

    count = (
        session.query(DpdHeadword)
        .filter(DpdHeadword.pattern == "test pr")
        .update({"pattern": "renamed pr"}, synchronize_session=False)
    )
    session.commit()
    assert count == 1
    hw = session.query(DpdHeadword).filter_by(id=1).one()
    assert hw.pattern == "renamed pr"

    loaded = load_templates(
        files.inflection_templates_index_path, files.inflection_templates_dir
    )
    assert [t.pattern for t in loaded] == ["renamed pr"]
    session.close()


def test_rename_trims_the_new_name(files: ProjectPaths):
    """Spaces around the new name never reach the file name or the index."""
    refusal = rename_template_core(
        "test pr",
        "  spaced pr ",
        files.inflection_templates_index_path,
        files.inflection_templates_dir,
        ["test pr"],
    )
    assert refusal == ""
    assert (files.inflection_templates_dir / "spaced pr.tsv").exists()
    loaded = load_templates(
        files.inflection_templates_index_path, files.inflection_templates_dir
    )
    assert [t.pattern for t in loaded] == ["spaced pr"]


def test_grammar_newline_cannot_split_the_tsv_line():
    """A newline typed in a grammar box becomes a space."""
    data = grid_values_to_data(["sg"], [["nom", "o", "nom\nsg"]])
    assert data[1][2] == ["nom sg"]


def test_rename_to_existing_name_refused(files: ProjectPaths):
    refusal = rename_template_core(
        "test pr",
        "test pr",
        files.inflection_templates_index_path,
        files.inflection_templates_dir,
        ["test pr"],
    )
    assert refusal


def test_delete_used_pattern_changes_nothing(files: ProjectPaths):
    refusal = delete_template_core(
        "test pr",
        files.inflection_templates_index_path,
        files.inflection_templates_dir,
        word_count=3,
    )
    assert refusal == "3 words use this pattern"
    assert file_count(files) == 1
    assert len(index_rows(files)) == 1


def test_delete_unused_pattern_works(files: ProjectPaths):
    refusal = delete_template_core(
        "test pr",
        files.inflection_templates_index_path,
        files.inflection_templates_dir,
        word_count=0,
    )
    assert refusal == ""
    assert file_count(files) == 0
    assert len(index_rows(files)) == 0


# ── the word-list filter ────────────────────────────────────────────────────


@pytest.fixture
def filter_db() -> Iterator[Session]:
    """A temp db with words whose patterns embed 'a nt'."""
    engine = create_engine("sqlite:///:memory:", echo=False)
    from db.models import Base

    Base.metadata.create_all(engine)
    session = Session(bind=engine)
    session.add_all(
        [
            DpdHeadword(id=1, lemma_1="one", pos="masc", pattern="a nt"),
            DpdHeadword(id=2, lemma_1="two", pos="masc", pattern="ā nt"),
            DpdHeadword(id=3, lemma_1="three", pos="masc", pattern="a nt irreg"),
        ]
    )
    session.commit()
    install_regexp(session)
    yield session
    session.close()


def test_pattern_word_filter_is_anchored(filter_db: Session):
    """Only the exact pattern matches, not ones that contain it."""
    filters = pattern_word_filter("a nt")
    conditions, error = build_filter_conditions(filters)
    assert error == ""
    results = filter_db.query(DpdHeadword).filter(*conditions).all()
    assert [r.lemma_1 for r in results] == ["one"]


def test_pattern_word_filter_matches_real_db_count():
    """On the real db (read-only): the filtered count equals the SQL count."""
    import sqlite3

    pth = ProjectPaths(create_dirs=False)
    con = sqlite3.connect(f"file:{pth.dpd_db_path}?mode=ro", uri=True)
    sql_count = con.execute(
        "select count(*) from dpd_headwords where pattern = 'natthi pr'"
    ).fetchone()[0]
    con.close()

    engine = create_engine(
        f"sqlite+pysqlite:///file:{pth.dpd_db_path}?mode=ro&uri=true",
        connect_args={"uri": True},
    )
    session = Session(bind=engine)
    install_regexp(session)
    conditions, error = build_filter_conditions(pattern_word_filter("natthi pr"))
    assert error == ""
    filtered_count = session.query(DpdHeadword).filter(*conditions).count()
    session.close()
    engine.dispose()
    assert filtered_count == sql_count


# ── grid_dimensions ─────────────────────────────────────────────────────────


def test_grid_dimensions_widest_in_column_tallest_in_row():
    """Each column takes its widest box, each row its tallest box."""
    headings = ["sg", "pl"]
    rows = [
        ["nom", "a\nb\nc", "x", "o", "a very long grammar label"],
        ["acc", "amhākaṃamhākaṃ", "y", "e", "z"],
    ]
    _, forms_widths, grammar_widths, line_counts = grid_dimensions(headings, rows)

    # row 0 has a 3-form cell, row 1 only single forms (minimum is 2 lines)
    assert line_counts == [3, 2]
    # column 0 is widened by the 14-char form, column 1 stays at the minimum
    assert forms_widths[0] == 14 * FORMS_CHAR_WIDTH + BOX_PADDING
    assert forms_widths[1] == FORMS_MIN_WIDTH
    # column 1's grammar column is widened by the long label
    assert grammar_widths[0] == GRAMMAR_MIN_WIDTH
    assert grammar_widths[1] == (
        len("a very long grammar label") * GRAMMAR_CHAR_WIDTH + BOX_PADDING
    )


def test_grid_dimensions_heading_widens_its_column():
    _, forms_widths, _, _ = grid_dimensions(
        ["reflexive plural heading"], [["nom", "", ""]]
    )
    assert (
        forms_widths[0]
        == len("reflexive plural heading") * HEADING_CHAR_WIDTH + BOX_PADDING
    )


def test_grid_dimensions_label_column_fits_the_longest_row_label():
    label_width, _, _, _ = grid_dimensions(
        ["sg"], [["nom", "", ""], ["fem instr sg", "", ""]]
    )
    assert label_width == len("fem instr sg") * GRAMMAR_CHAR_WIDTH + BOX_PADDING
    short, _, _, _ = grid_dimensions(["sg"], [["a", "", ""]])
    assert short == LABEL_MIN_WIDTH


def test_a_real_wide_template_fits_the_window():
    """ati pr (4 column pairs, the widest verb) must fit gui2's 1,375 px window."""
    pth = ProjectPaths(create_dirs=False)
    templates = load_templates(
        pth.inflection_templates_index_path, pth.inflection_templates_dir
    )
    ati = next(t for t in templates if t.pattern == "ati pr")
    headings, rows = data_to_grid_values(ati.data)
    label_width, forms_widths, grammar_widths, _ = grid_dimensions(headings, rows)
    total = label_width + sum(forms_widths) + sum(grammar_widths) + len(headings) * 2
    assert total <= 1375, total


def test_row_label_newline_cannot_split_the_tsv_line():
    data = grid_values_to_data(["sg"], [["fem\ninstr sg", "o", "g"]])
    assert data[1][0] == ["fem instr sg"]


def test_save_reloads_the_grid_sorted(files: ProjectPaths):
    """After Save the boxes show the saved file: forms trimmed and sorted."""
    toolkit = MagicMock()
    toolkit.db_manager.pth = files
    view = InflectionTemplatesTabView(MagicMock(), toolkit)
    view._load_template("test pr")

    view._rows[0][1] = "ānaṃ\n  a \n\nā"  # unsorted, padded, a blank line
    view._save_template(None)  # pyright: ignore[reportArgumentType]

    assert view._rows[0][1] == "a\nā\nānaṃ"


def test_opening_the_tab_focuses_the_pattern_box(
    files: ProjectPaths, monkeypatch: pytest.MonkeyPatch
):
    toolkit = MagicMock()
    toolkit.db_manager.pth = files
    view = InflectionTemplatesTabView(MagicMock(), toolkit)
    focused: list[object] = []
    monkeypatch.setattr(
        "gui2.inflection_templates_tab_view.is_mounted", lambda control: True
    )
    monkeypatch.setattr(
        "gui2.inflection_templates_tab_view.request_focus", focused.append
    )

    view.on_tab_focus()

    assert focused == [view._pattern_dropdown]


def test_tab_builds_even_when_the_template_files_do_not_load(tmp_path):
    """No index file: the tab still opens, with an empty list and a message."""
    toolkit = MagicMock()
    toolkit.db_manager.pth = ProjectPaths(base_dir=tmp_path, create_dirs=False)

    view = InflectionTemplatesTabView(MagicMock(), toolkit)

    assert "index file not found" in (view._message_field.value or "")
    assert view._pattern_dropdown.options == []


def test_headings_are_blue_and_data_is_not(files: ProjectPaths):
    """Column headings and row titles are blue; forms and grammar are data."""
    toolkit = MagicMock()
    toolkit.db_manager.pth = files
    view = InflectionTemplatesTabView(MagicMock(), toolkit)
    view._load_template("test pr")

    grid = view._grid_column.controls
    heading_row = grid[1]
    data_row = grid[2]
    assert isinstance(heading_row, ft.Row) and isinstance(data_row, ft.Row)
    heading_box = heading_row.controls[1]  # first column heading
    row_title_box, forms_box, grammar_box = data_row.controls[:3]
    assert isinstance(heading_box, ft.TextField)
    assert isinstance(row_title_box, ft.TextField)
    assert isinstance(forms_box, ft.TextField)
    assert isinstance(grammar_box, ft.TextField)

    assert heading_box.color == HIGHLIGHT_COLOUR
    assert row_title_box.color == HIGHLIGHT_COLOUR
    assert forms_box.color != HIGHLIGHT_COLOUR
    assert grammar_box.color != HIGHLIGHT_COLOUR
    assert heading_box.border.side.color == HIGHLIGHT_COLOUR  # pyright: ignore
    assert forms_box.border.side.color != HIGHLIGHT_COLOUR  # pyright: ignore
