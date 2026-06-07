import json
from pathlib import Path

from db.suttas.suttas_update import _prepare_sutta_row

FIXTURE_PATH = Path(__file__).parent / "test_suttas_update_fixtures.json"
_FIXTURES = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
_MODEL_COLUMNS = set(_FIXTURES["model_columns"])
_CASES = _FIXTURES["cases"]


def test_prepare_sutta_row_matches_frozen_inline_output() -> None:
    """Golden master: extracted helper reproduces the original inline transform
    byte-for-byte on real TSV rows."""
    for name, case in _CASES.items():
        result = _prepare_sutta_row(case["input"], _MODEL_COLUMNS)
        assert result == case["output"], f"mismatch on case {name}"


def test_prepare_sutta_row_filters_to_model_columns() -> None:
    row = {"dpd_sutta": "x", "not_a_column": "drop me", "cst_code": "dn1"}
    result = _prepare_sutta_row(row, _MODEL_COLUMNS)
    assert "not_a_column" not in result
    assert result["dpd_sutta"] == "x"


def test_prepare_sutta_row_uppercases_codes() -> None:
    row = {"cst_code": "dn1.1", "dpr_code": "dn1", "sc_code": "dn1"}
    result = _prepare_sutta_row(row, _MODEL_COLUMNS)
    assert result["cst_code"] == "DN1.1"
    assert result["dpr_code"] == "DN1"
    assert result["sc_code"] == "DN1"


def test_prepare_sutta_row_pads_short_page_numbers() -> None:
    row = {"cst_m_page": "1.5", "cst_v_page": "10.23"}
    result = _prepare_sutta_row(row, _MODEL_COLUMNS)
    assert result["cst_m_page"] == "1.5000"
    assert result["cst_v_page"] == "10.2300"


def test_prepare_sutta_row_leaves_padded_page_numbers() -> None:
    row = {"cst_m_page": "1.0001"}
    result = _prepare_sutta_row(row, _MODEL_COLUMNS)
    assert result["cst_m_page"] == "1.0001"


def test_prepare_sutta_row_ignores_empty_and_pageless_values() -> None:
    row = {"cst_m_page": "", "cst_v_page": "5"}
    result = _prepare_sutta_row(row, _MODEL_COLUMNS)
    assert result["cst_m_page"] == ""
    assert result["cst_v_page"] == "5"
