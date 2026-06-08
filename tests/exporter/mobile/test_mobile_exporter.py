import json
import importlib
import sqlite3
import sys
from pathlib import Path
from types import ModuleType, SimpleNamespace

import pytest

aksharamukha_stub = ModuleType("aksharamukha")
setattr(aksharamukha_stub, "transliterate", SimpleNamespace())
sys.modules.setdefault("aksharamukha", aksharamukha_stub)

FIXTURES = json.loads(
    (Path(__file__).parent / "test_mobile_exporter_fixtures.json").read_text(
        encoding="utf-8"
    )
)


def _mod() -> ModuleType:
    return importlib.import_module("exporter.mobile.mobile_exporter")


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
        bhs_source_path=tmp_path / "bhs.xml",
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


@pytest.mark.parametrize(
    "text,expected", list(FIXTURES["strip_diacritics_mobile"].items())
)
def test_strip_diacritics_mobile_matches_fixture(text: str, expected: str) -> None:
    assert _mod()._strip_diacritics_mobile(text) == expected


@pytest.mark.parametrize("lemma,expected", list(FIXTURES["lemma_clean"].items()))
def test_lemma_clean_matches_fixture(lemma: str, expected: str) -> None:
    assert _mod()._lemma_clean(lemma) == expected


def _make_source_db(tmp_path: Path) -> Path:
    src_path = tmp_path / "source.db"
    con = sqlite3.connect(src_path)
    con.executescript(
        """
        CREATE TABLE lookup (lookup_key TEXT, headwords TEXT, deconstructor TEXT);
        CREATE INDEX idx_src_lookup_headwords ON lookup (headwords);
        CREATE TABLE db_info (key TEXT PRIMARY KEY, value TEXT);
        CREATE INDEX idx_src_dbinfo_value ON db_info (value);
        CREATE TABLE inflection_templates (pattern TEXT, data TEXT);
        CREATE TABLE family_root (
            root_family_key TEXT, root_key TEXT, root_family TEXT,
            root_meaning TEXT, html TEXT, data TEXT, count INTEGER
        );
        CREATE TABLE family_word (word_family TEXT, data TEXT, count INTEGER, extra TEXT);
        CREATE TABLE family_compound (compound_family TEXT, data TEXT, count INTEGER);
        CREATE TABLE family_idiom (idiom TEXT, data TEXT, count INTEGER);
        CREATE TABLE "family_set" ("set" TEXT, data TEXT, count INTEGER);
        """
    )
    con.executemany(
        "INSERT INTO lookup VALUES (?, ?, ?)",
        [("saṃyutta", "[1,2]", ""), ("√gam", "[3]", "x"), ("buddha", "[4]", "")],
    )
    con.executemany("INSERT INTO db_info VALUES (?, ?)", [("a", "1"), ("b", "2")])
    con.execute("INSERT INTO inflection_templates VALUES (?, ?)", ("masc", "grid"))
    con.execute(
        "INSERT INTO family_root VALUES (?, ?, ?, ?, ?, ?, ?)",
        ("√gam 1", "√gam", "√gam group", "go", "<b>h</b>", "d", 5),
    )
    con.execute(
        "INSERT INTO family_word VALUES (?, ?, ?, ?)", ("gam", "d", 3, "DROPME")
    )
    con.execute("INSERT INTO family_compound VALUES (?, ?, ?)", ("cpd", "d", 2))
    con.execute("INSERT INTO family_idiom VALUES (?, ?, ?)", ("idi", "d", 1))
    con.execute('INSERT INTO "family_set" VALUES (?, ?, ?)', ("set1", "d", 4))
    con.commit()
    con.close()
    return src_path


def _g_for(src_path: Path) -> SimpleNamespace:
    src = sqlite3.connect(src_path)
    src.row_factory = sqlite3.Row
    return SimpleNamespace(pth=SimpleNamespace(dpd_db_path=src_path), src=src)


def test_export_lookup_adds_fuzzy_key_primary_key_and_replicates_index(
    tmp_path: Path,
) -> None:
    module = _mod()
    g = _g_for(_make_source_db(tmp_path))
    dest = sqlite3.connect(":memory:")

    module.export_lookup(g, dest)

    rows = {
        r[0]: (r[1], r[2], r[3])
        for r in dest.execute(
            "SELECT lookup_key, headwords, deconstructor, fuzzy_key FROM lookup"
        ).fetchall()
    }
    assert rows == {
        "saṃyutta": ("[1,2]", "", module._strip_diacritics_mobile("saṃyutta")),
        "√gam": ("[3]", "x", module._strip_diacritics_mobile("√gam")),
        "buddha": ("[4]", "", module._strip_diacritics_mobile("buddha")),
    }

    with pytest.raises(sqlite3.IntegrityError):
        dest.execute("INSERT INTO lookup VALUES ('buddha', '[9]', '', 'x')")

    indexes = {
        r[0]
        for r in dest.execute(
            "SELECT name FROM sqlite_master WHERE type='index'"
        ).fetchall()
    }
    assert "idx_lookup_fuzzy_key" in indexes
    assert "idx_src_lookup_headwords" in indexes


def test_copy_passthrough_copies_present_tables_and_skips_absent(
    tmp_path: Path,
) -> None:
    module = _mod()
    g = _g_for(_make_source_db(tmp_path))
    dest = sqlite3.connect(":memory:")

    module.copy_passthrough_tables(g, dest)

    names = {
        r[0]
        for r in dest.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
    }
    assert "db_info" in names
    assert "inflection_templates" in names
    assert "sutta_info" not in names

    assert dest.execute("SELECT key, value FROM db_info ORDER BY key").fetchall() == [
        ("a", "1"),
        ("b", "2"),
    ]
    with pytest.raises(sqlite3.IntegrityError):
        dest.execute("INSERT INTO db_info VALUES ('a', 'dup')")

    indexes = {
        r[0]
        for r in dest.execute(
            "SELECT name FROM sqlite_master WHERE type='index'"
        ).fetchall()
    }
    assert "idx_src_dbinfo_value" in indexes


def test_copy_family_tables_selects_columns_and_drops_extras(tmp_path: Path) -> None:
    module = _mod()
    g = _g_for(_make_source_db(tmp_path))
    dest = sqlite3.connect(":memory:")

    module.copy_family_tables(g, dest)

    word_cols = [
        r[1] for r in dest.execute("PRAGMA table_info(family_word)").fetchall()
    ]
    assert word_cols == ["word_family", "data", "count"]
    assert dest.execute("SELECT * FROM family_word").fetchall() == [("gam", "d", 3)]
    assert dest.execute(
        "SELECT root_family_key, html, count FROM family_root"
    ).fetchone() == ("√gam 1", "<b>h</b>", 5)

    for table in (
        "family_root",
        "family_word",
        "family_compound",
        "family_idiom",
        "family_set",
    ):
        assert dest.execute(f'SELECT COUNT(*) FROM "{table}"').fetchone()[0] == 1
