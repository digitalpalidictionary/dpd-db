"""Characterization tests for scripts/build/families_to_json.py.

Guards the refactor only — behaviour-preserving changes (param rename, pathlib
open, type hints, alias removal). Inputs frozen in fixture file; no live DB.
"""

import json
import tempfile
from pathlib import Path
from types import SimpleNamespace

from scripts.build.families_to_json import (
    export_family_compound,
    export_family_idiom,
    export_family_root,
    export_family_set,
    export_family_word,
    json_dumper,
)

FIXTURE_PATH = Path(__file__).parent / "test_families_to_json_fixtures.json"


def _fixtures() -> dict:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def _make_g(tmp_dir: Path, fixtures: dict) -> SimpleNamespace:
    """Build a minimal GlobalVars stand-in with stub DB rows and temp paths."""

    def _rows(
        d: dict, key_field: str, extra_fields: list[str] | None = None
    ) -> list[SimpleNamespace]:
        rows = []
        for key, val in d.items():
            attrs = {key_field: key, "count": val["count"]}
            attrs["data_unpack"] = val["data"]
            for f in extra_fields or []:
                attrs[f] = val[f]
            rows.append(SimpleNamespace(**attrs))
        return rows

    fx = fixtures
    paths = SimpleNamespace(
        family_compound_json=tmp_dir / "family_compound_json.js",
        family_idiom_json=tmp_dir / "family_idiom_json.js",
        family_root_json=tmp_dir / "family_root_json.js",
        family_set_json=tmp_dir / "family_set_json.js",
        family_word_json=tmp_dir / "family_word_json.js",
    )
    return SimpleNamespace(
        paths=paths,
        fc_db=_rows(fx["fc_dict"], "compound_family"),
        fi_db=_rows(fx["fi_dict"], "idiom"),
        fr_db=_rows(
            fx["fr_dict"],
            "root_family_key",
            ["root_key", "root_family", "root_meaning"],
        ),
        fs_db=_rows(fx["fs_dict"], "set"),
        fw_db=_rows(fx["fw_dict"], "word_family"),
    )


def test_json_dumper_format() -> None:
    """Output must be a JS variable assignment: var <stem> = <json>."""
    fixtures = _fixtures()
    data = fixtures["fc_dict"]
    with tempfile.TemporaryDirectory() as td:
        path = Path(td) / "family_compound_json.js"
        json_dumper(path, data)
        content = path.read_text(encoding="utf-8")
    assert content.startswith("var family_compound_json = ")
    parsed = json.loads(content[len("var family_compound_json = ") :])
    assert parsed == data


def test_export_family_compound() -> None:
    fixtures = _fixtures()
    with tempfile.TemporaryDirectory() as td:
        g = _make_g(Path(td), fixtures)
        export_family_compound(g)
        content = g.paths.family_compound_json.read_text(encoding="utf-8")
    assert content.startswith("var family_compound_json = ")
    result = json.loads(content[len("var family_compound_json = ") :])
    assert result == fixtures["fc_dict"]


def test_export_family_idiom() -> None:
    fixtures = _fixtures()
    with tempfile.TemporaryDirectory() as td:
        g = _make_g(Path(td), fixtures)
        export_family_idiom(g)
        content = g.paths.family_idiom_json.read_text(encoding="utf-8")
    assert content.startswith("var family_idiom_json = ")
    result = json.loads(content[len("var family_idiom_json = ") :])
    assert result == fixtures["fi_dict"]


def test_export_family_root_has_extra_fields() -> None:
    fixtures = _fixtures()
    with tempfile.TemporaryDirectory() as td:
        g = _make_g(Path(td), fixtures)
        export_family_root(g)
        content = g.paths.family_root_json.read_text(encoding="utf-8")
    assert content.startswith("var family_root_json = ")
    result = json.loads(content[len("var family_root_json = ") :])
    assert result == fixtures["fr_dict"]
    for entry in result.values():
        assert "root_key" in entry
        assert "root_family" in entry
        assert "root_meaning" in entry


def test_export_family_set() -> None:
    fixtures = _fixtures()
    with tempfile.TemporaryDirectory() as td:
        g = _make_g(Path(td), fixtures)
        export_family_set(g)
        content = g.paths.family_set_json.read_text(encoding="utf-8")
    assert content.startswith("var family_set_json = ")
    result = json.loads(content[len("var family_set_json = ") :])
    assert result == fixtures["fs_dict"]


def test_export_family_word() -> None:
    fixtures = _fixtures()
    with tempfile.TemporaryDirectory() as td:
        g = _make_g(Path(td), fixtures)
        export_family_word(g)
        content = g.paths.family_word_json.read_text(encoding="utf-8")
    assert content.startswith("var family_word_json = ")
    result = json.loads(content[len("var family_word_json = ") :])
    assert result == fixtures["fw_dict"]
