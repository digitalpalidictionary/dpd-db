"""A single Kindle index term resolves to a single entry, so a form shared by
several headwords must get its own entry listing them all. These tests pin that
routing: sole-owner forms become aliases, ambiguous forms become linked entries."""

from types import SimpleNamespace
from typing import cast

from db.models import DpdHeadword
from exporter.jinja2_env import get_jinja2_env
from exporter.kindle import kindle_exporter
from exporter.kindle.data_classes import KindleData


def _env():
    return get_jinja2_env("exporter/kindle/templates")


def _data(id_: int, lemma_1: str, summary: str = "adj. test") -> KindleData:
    return cast(
        KindleData,
        SimpleNamespace(
            i=SimpleNamespace(id=id_, lemma_1=lemma_1),
            summary=summary,
            grammar_table="",
            examples="",
        ),
    )


def _headword(id_: int, lemma_1: str) -> DpdHeadword:
    return cast(DpdHeadword, SimpleNamespace(id=id_, lemma_1=lemma_1))


def test_letter_files_match_the_static_manifest() -> None:
    """content.opf hardcodes the filenames, so the mapping must not drift."""
    files = kindle_exporter._letter_files()
    assert files["a"] == "0_a.xhtml"
    assert len(files) == len(set(files.values()))


def test_headword_aliases_cover_own_forms_and_scripts_but_not_the_label() -> None:
    headword = _headword(7, "gacchati 1")
    aliases = kindle_exporter._headword_aliases(
        headword,
        {7: ["gacchāmi", "gacchati 1"]},
        {"gacchāmi": ["गच्छामि"], "gacchati 1": ["गच्छति"]},
    )
    assert "gacchāmi" in aliases
    assert "गच्छामि" in aliases
    assert "गच्छति" in aliases
    assert "gacchati 1" not in aliases


def test_a_form_entry_lists_every_sense_with_a_link() -> None:
    html = kindle_exporter.render_form_entry(
        _env(),
        1,
        "gacchati",
        [_data(24043, "gacchati 1"), _data(24044, "gacchati 2")],
        [],
        None,
        "",
        {"g": "10_g.xhtml"},
    )
    assert '<idx:orth value="gacchati">' in html
    assert '<a href="10_g.xhtml#hw24043"><b>gacchati 1</b></a>' in html
    assert '<a href="10_g.xhtml#hw24044"><b>gacchati 2</b></a>' in html


def test_a_contested_label_carries_both_the_list_and_the_headword_detail() -> None:
    merged = _data(928, "acca", "masc. a merged headword")
    html = kindle_exporter.render_form_entry(
        _env(),
        2,
        "acca",
        [_data(35345, "accati 1")],
        [],
        merged,
        "",
        {"a": "0_a.xhtml"},
    )
    assert '<idx:orth value="acca">' in html
    assert 'href="0_a.xhtml#hw35345"' in html
    assert 'id="hw928"' in html
    assert "a merged headword" in html


def test_script_spellings_attach_as_aliases() -> None:
    html = kindle_exporter.render_form_entry(
        _env(),
        3,
        "dhammo",
        [_data(1, "dhamma 1")],
        ["धम्मो", "ธมฺโม"],
        None,
        "",
        {"dh": "21_dh.xhtml"},
    )
    assert '<idx:iform value="धम्मो" exact="yes">' in html
    assert '<idx:iform value="ธมฺโม" exact="yes">' in html


def test_a_headword_entry_is_labelled_with_lemma_1_not_lemma_clean() -> None:
    """lemma_clean was the bug: 13 `uttara` homonyms shared one label and 12
    became unreachable."""
    html = kindle_exporter.render_ebook_entry(
        _env(), _data(14657, "uttara 1.1"), ["uttaro"], ""
    )
    assert '<idx:orth value="uttara 1.1">' in html
    assert 'id="hw14657"' in html
    assert '<idx:iform value="uttaro" exact="yes">' in html
