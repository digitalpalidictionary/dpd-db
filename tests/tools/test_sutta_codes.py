# ruff: noqa: E402

import sys
import types

_aksharamukha_stub = types.ModuleType("aksharamukha")
setattr(
    _aksharamukha_stub,
    "transliterate",
    types.SimpleNamespace(process=lambda *_, **__: ""),
)
sys.modules.setdefault("aksharamukha", _aksharamukha_stub)

import pytest

from db.models import SuttaInfo
from tools.sutta_codes import make_list_of_sutta_codes


@pytest.mark.parametrize("sc_code", ["", " ", "\t "])
def test_make_list_of_sutta_codes_skips_blank_sc_code(sc_code: str) -> None:
    su = SuttaInfo()
    su.dpd_sutta = "yonisomanasikārasutta"
    su.dpd_code = "SN46.36"
    su.sc_code = sc_code

    assert make_list_of_sutta_codes(su) == ["SN46.36"]


def test_make_list_of_sutta_codes_skips_sc_code_for_samyutta_rows() -> None:
    su = SuttaInfo()
    su.dpd_sutta = "devatāsaṃyutta"
    su.dpd_code = "SN1"
    su.sc_code = "SN1.1"

    assert make_list_of_sutta_codes(su) == ["SN1"]


def test_make_list_of_sutta_codes_skips_sc_code_for_vagga_rows() -> None:
    su = SuttaInfo()
    su.dpd_sutta = "buddhavagga"
    su.dpd_code = "AN8.1-10"
    su.sc_code = "AN8.1"
    su.sc_vagga = "1. Mettāvagga"

    assert make_list_of_sutta_codes(su) == [
        "AN8.1",
        "AN8.1-10",
        "AN8.10",
        "AN8.2",
        "AN8.3",
        "AN8.4",
        "AN8.5",
        "AN8.6",
        "AN8.7",
        "AN8.8",
        "AN8.9",
    ]
