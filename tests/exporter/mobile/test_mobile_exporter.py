import json
import importlib
import sqlite3
import sys
from pathlib import Path
from types import ModuleType, SimpleNamespace

aksharamukha_stub = ModuleType("aksharamukha")
setattr(aksharamukha_stub, "transliterate", SimpleNamespace())
sys.modules.setdefault("aksharamukha", aksharamukha_stub)


def _export_other_dictionaries(*args, **kwargs) -> None:
    module = importlib.import_module("exporter.mobile.mobile_exporter")
    module.export_other_dictionaries(*args, **kwargs)


def _write_json(path: Path, data: dict[str, str] | list[dict[str, str]]) -> None:
    path.write_text(json.dumps(data), encoding="utf-8")


def _write_cpd_db(path: Path, rows: list[tuple[str, str]]) -> None:
    with sqlite3.connect(path) as conn:
        conn.execute(
            "CREATE TABLE entries (id INTEGER PRIMARY KEY, headword TEXT, html TEXT)"
        )
        conn.executemany(
            "INSERT INTO entries (id, headword, html) VALUES (?, ?, ?)",
            [
                (index, headword, html)
                for index, (headword, html) in enumerate(rows, start=1)
            ],
        )


def _make_paths(tmp_path: Path) -> SimpleNamespace:
    return SimpleNamespace(
        cone_source_path=tmp_path / "cone.json",
        cone_css_path=tmp_path / "cone.css",
        mw_source_json_path=tmp_path / "mw.json",
        mw_css_path=tmp_path / "mw.css",
        cpd_source_path=tmp_path / "cpd_clean.db",
        cpd_css_path=tmp_path / "cpd.css",
    )


def _export(tmp_path: Path, *, include_cone: bool = True) -> sqlite3.Connection:
    dest = sqlite3.connect(":memory:")
    _export_other_dictionaries(
        SimpleNamespace(pth=_make_paths(tmp_path)),
        dest,
        include_cone=include_cone,
    )
    return dest


def test_exports_cpd_entries_with_canonical_headword_and_stripped_images(
    tmp_path: Path,
) -> None:
    paths = _make_paths(tmp_path)
    _write_json(paths.cone_source_path, {"1kamma": "<p>Cone entry</p>"})
    paths.cone_css_path.write_text(".cone { color: blue; }", encoding="utf-8")
    _write_json(
        paths.mw_source_json_path,
        [{"word": "dharma", "definition_html": "<p>MW entry</p>"}],
    )
    paths.mw_css_path.write_text(".mw { color: green; }", encoding="utf-8")
    _write_cpd_db(
        paths.cpd_source_path,
        [("saṁkhāra", "<p>CPD</p><img src='x.png'><div>entry</div>")],
    )
    paths.cpd_css_path.write_text(
        ".cpd { color: black; position: fixed; color: maroon; }", encoding="utf-8"
    )

    dest = _export(tmp_path)

    row = dest.execute(
        "SELECT word, word_fuzzy, definition_html, definition_plain FROM dict_entries WHERE dict_id = 'cpd'"
    ).fetchone()

    assert row == (
        "saṃkhāra",
        "samkara",
        "<p>CPD</p><div>entry</div>",
        "",
    )


def test_exports_cpd_metadata_with_sanitized_css(tmp_path: Path) -> None:
    paths = _make_paths(tmp_path)
    _write_json(paths.mw_source_json_path, [])
    paths.mw_css_path.write_text(".mw { color: green; }", encoding="utf-8")
    _write_cpd_db(paths.cpd_source_path, [("aṁga", "<p>entry</p>")])
    paths.cpd_css_path.write_text(
        ".cpd { color: black; background-color: white; color: maroon; }",
        encoding="utf-8",
    )

    dest = _export(tmp_path, include_cone=False)

    row = dest.execute(
        "SELECT dict_id, name, author, css, entry_count FROM dict_meta WHERE dict_id = 'cpd'"
    ).fetchone()

    assert row[0] == "cpd"
    assert row[1] == "Critical Pali Dictionary"
    assert row[2] == "V. Trenckner et al."
    assert "color: black" not in row[3]
    assert "background-color: white" not in row[3]
    assert "color: maroon" in row[3]
    assert row[4] == 1


def test_skips_missing_cpd_source_and_keeps_existing_dictionary_exports(
    tmp_path: Path,
) -> None:
    paths = _make_paths(tmp_path)
    _write_json(paths.cone_source_path, {"1kamma": "<p>Cone entry</p>"})
    paths.cone_css_path.write_text(".cone { color: blue; }", encoding="utf-8")
    _write_json(
        paths.mw_source_json_path,
        [{"word": "dharma", "definition_html": "<p>MW entry</p>"}],
    )
    paths.mw_css_path.write_text(".mw { color: green; }", encoding="utf-8")

    dest = _export(tmp_path)

    dict_ids = {
        row[0]
        for row in dest.execute(
            "SELECT dict_id FROM dict_meta ORDER BY dict_id"
        ).fetchall()
    }

    assert dict_ids == {"cone", "mw"}
    assert (
        dest.execute(
            "SELECT COUNT(*) FROM dict_entries WHERE dict_id = 'cpd'"
        ).fetchone()[0]
        == 0
    )


def test_preserves_duplicate_cpd_source_rows_without_alias_rows(tmp_path: Path) -> None:
    paths = _make_paths(tmp_path)
    _write_json(paths.mw_source_json_path, [])
    paths.mw_css_path.write_text(".mw { color: green; }", encoding="utf-8")
    _write_cpd_db(
        paths.cpd_source_path,
        [
            ("aṁga", "<p>first</p>"),
            ("aṁga", "<p>second</p>"),
        ],
    )
    paths.cpd_css_path.write_text(".cpd { color: maroon; }", encoding="utf-8")

    dest = _export(tmp_path, include_cone=False)

    rows = dest.execute(
        "SELECT word, definition_html FROM dict_entries WHERE dict_id = 'cpd' ORDER BY id"
    ).fetchall()
    counts = dest.execute(
        "SELECT COUNT(*), COUNT(DISTINCT word) FROM dict_entries WHERE dict_id = 'cpd'"
    ).fetchone()

    assert rows == [
        ("aṃga", "<p>first</p>"),
        ("aṃga", "<p>second</p>"),
    ]
    assert counts == (2, 1)
    assert (
        dest.execute(
            "SELECT COUNT(*) FROM dict_entries WHERE dict_id = 'cpd' AND word IN ('aṁga', 'aŋga')"
        ).fetchone()[0]
        == 0
    )


def test_exports_cpd_with_empty_css_when_stylesheet_is_missing(tmp_path: Path) -> None:
    paths = _make_paths(tmp_path)
    _write_json(paths.mw_source_json_path, [])
    paths.mw_css_path.write_text(".mw { color: green; }", encoding="utf-8")
    _write_cpd_db(paths.cpd_source_path, [("aṁga", "<p>entry</p>")])

    dest = _export(tmp_path, include_cone=False)

    row = dest.execute(
        "SELECT css, entry_count FROM dict_meta WHERE dict_id = 'cpd'"
    ).fetchone()

    assert row == ("", 1)


def test_full_export_keeps_cone_and_mw_outputs_alongside_cpd(tmp_path: Path) -> None:
    paths = _make_paths(tmp_path)
    _write_json(
        paths.cone_source_path,
        {"1kamma": '<!DOCTYPE html><html><body><a href="x">Cone</a></body></html>'},
    )
    paths.cone_css_path.write_text(".cone { color: blue; }", encoding="utf-8")
    _write_json(
        paths.mw_source_json_path,
        [{"word": "dharma", "definition_html": "<p>MW entry</p>"}],
    )
    paths.mw_css_path.write_text(".mw { color: green; }", encoding="utf-8")
    _write_cpd_db(paths.cpd_source_path, [("aṁga", "<p>CPD entry</p>")])
    paths.cpd_css_path.write_text(".cpd { color: maroon; }", encoding="utf-8")

    dest = _export(tmp_path)

    rows = dest.execute(
        "SELECT dict_id, word, word_fuzzy, definition_html FROM dict_entries ORDER BY dict_id, id"
    ).fetchall()

    assert rows == [
        ("cone", "kamma", "kama", '<span class="blue">Cone</span>'),
        ("cpd", "aṃga", "amga", "<p>CPD entry</p>"),
        ("mw", "dharma", "darma", "<p>MW entry</p>"),
    ]


def test_paths_point_to_cpd_sqlite_source_and_stylesheet() -> None:
    from tools.paths import ProjectPaths

    paths = ProjectPaths(Path("/repo"), create_dirs=False)

    assert paths.cpd_source_path == Path(
        "/repo/resources/other-dictionaries/dictionaries/cpd/source/cpd_clean.db"
    )
    assert paths.cpd_css_path == Path(
        "/repo/resources/other-dictionaries/dictionaries/cpd/cpd.css"
    )
