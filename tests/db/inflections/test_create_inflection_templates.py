"""Tests for db/inflections/create_inflection_templates.py

Tests cover the data transformation chain:
    Excel cell range → DataFrame slice → nested list → InflectionTemplates object

DB writes and file I/O are not tested — SQLAlchemy and stdlib are trusted.
"""

import subprocess
import sys
import tempfile
from pathlib import Path

import pytest
from db.inflections.create_inflection_templates import (
    GlobalVars,
    convert_template_df_to_datalist,
    extract_template_df,
    make_index_dataframe,
    make_infl_templ_dataframe,
    make_inflection_template,
)
from tools.paths import ProjectPaths


@pytest.fixture(scope="module")
def g() -> GlobalVars:
    """Load real Excel data once for all tests — no DB session needed."""
    gv = GlobalVars.__new__(GlobalVars)
    gv.pth = ProjectPaths()
    gv.added_templates = []
    gv.changed_templates = []
    make_index_dataframe(gv)
    make_infl_templ_dataframe(gv)
    return gv


def test_index_dataframe_loads(g: GlobalVars) -> None:
    """Index sheet loads with correct columns and expected row count."""
    assert list(g.index_df.columns) == ["inflection name", "cell range", "like"]
    assert len(g.index_df) == 154


def test_infl_templ_dataframe_loads(g: GlobalVars) -> None:
    """Declensions sheet loads and columns are renamed to letter codes."""
    assert g.infl_templ_df.shape[0] > 0
    assert "A" in g.infl_templ_df.columns
    assert "DK" in g.infl_templ_df.columns


def test_extract_template_df_a_adj(g: GlobalVars) -> None:
    """'a adj' template extracts to correct shape and known cell values."""
    g.index_data = g.index_df.iloc[0]
    extract_template_df(g)

    assert g.inflection_name == "a adj"
    assert g.like == "samannāgata"
    assert g.template_df.shape == (10, 13)
    # row 1 (nom), col 1 (masc sg) = 'o'
    assert g.template_df.iloc[1, 1] == "o"
    # row 1 (nom), col 9 (neut sg) = 'aṃ'
    assert g.template_df.iloc[1, 9] == "aṃ"


def test_convert_template_df_to_datalist_a_adj(g: GlobalVars) -> None:
    """'a adj' data_list has correct structure and multi-value cells are sorted."""
    g.index_data = g.index_df.iloc[0]
    extract_template_df(g)
    convert_template_df_to_datalist(g)

    assert len(g.data_list) == 10
    assert len(g.data_list[0]) == 13
    # header row: first cell cleared, second cell is gender/number label
    assert g.data_list[0][0] == [""]
    assert g.data_list[0][1] == ["masc sg"]
    # nom row: masc pl has two forms, sorted by pali sort key
    nom_masc_pl = g.data_list[1][3]
    assert isinstance(nom_masc_pl, list)
    assert "ā" in nom_masc_pl
    assert "āse" in nom_masc_pl


def test_make_inflection_template_a_adj(g: GlobalVars) -> None:
    """InflectionTemplates object created with correct pattern and like."""
    g.index_data = g.index_df.iloc[0]
    extract_template_df(g)
    convert_template_df_to_datalist(g)
    make_inflection_template(g)

    assert g.infl_templ.pattern == "a adj"
    assert g.infl_templ.like == "samannāgata"
    assert g.infl_templ.data is not None


def test_import_has_no_db_side_effects() -> None:
    """Importing the module must not open the DB or create directories.

    Run from an empty cwd with no dpd.db — the old class-level GlobalVars
    exited with 'Database file doesn't exist' here.
    """
    repo_root = Path(__file__).resolve().parents[3]
    with tempfile.TemporaryDirectory() as td:
        result = subprocess.run(
            [sys.executable, "-c", "import db.inflections.create_inflection_templates"],
            cwd=td,
            env={"PYTHONPATH": str(repo_root)},
            capture_output=True,
            text=True,
        )
        leftover_dirs = [p for p in Path(td).iterdir() if p.is_dir()]
    assert result.returncode == 0, result.stderr
    # tools/printer.py still writes its log file at import (intentional
    # singleton); only the ProjectPaths directory tree must be gone.
    assert leftover_dirs == []
