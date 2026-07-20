# ruff: noqa: E402

import sys
import types

sys.modules.setdefault(
    "aksharamukha",
    types.SimpleNamespace(
        transliterate=types.SimpleNamespace(process=lambda *args, **kwargs: "")
    ),
)

from db.models import SuttaInfo


def test_sutta_info_marks_sn_collection_as_samyutta() -> None:
    su = SuttaInfo()
    su.dpd_sutta = "devatāsaṃyutta"
    su.dpd_code = "SN1"

    assert su.is_samyutta is True
    assert su.is_vagga is False


def test_sutta_info_marks_vagga_samyuttapali_as_vagga() -> None:
    su = SuttaInfo()
    su.dpd_sutta = "sagāthāvaggasaṃyuttapāḷi"
    su.dpd_code = "SN1-11"
    su.sc_vagga = "1. Naḷavagga"

    assert su.is_samyutta is False
    assert su.is_vagga is True


def test_sutta_info_s_4nt_link_dn_mn_are_per_sutta_pages() -> None:
    su = SuttaInfo()
    su.sc_code = "MN125"
    assert su.s_4nt_link == "https://s.4nt.org/mn/mn125/index.html"

    su = SuttaInfo()
    su.sc_code = "DN24"
    assert su.s_4nt_link == "https://s.4nt.org/dn/dn24/index.html"


def test_sutta_info_s_4nt_link_sn_links_to_exact_sutta_anchor() -> None:
    su = SuttaInfo()
    su.sc_code = "SN1.1"

    assert su.s_4nt_link == "https://s.4nt.org/sn/sn1/index.html#sn1.1"


def test_sutta_info_s_4nt_link_an_links_to_exact_sutta_anchor() -> None:
    su = SuttaInfo()
    su.sc_code = "AN3.65"

    assert su.s_4nt_link == "https://s.4nt.org/an/an3/index.html#an3.65"


def test_sutta_info_s_4nt_link_an_bare_nipata_code_links_to_own_container() -> None:
    su = SuttaInfo()
    su.sc_code = "AN5"

    assert su.s_4nt_link == "https://s.4nt.org/an/an5/index.html"


def test_sutta_info_s_4nt_link_range_code_that_is_itself_a_real_anchor() -> None:
    su = SuttaInfo()
    su.sc_code = "SN39.1-15"

    assert su.s_4nt_link == "https://s.4nt.org/sn/sn39/index.html#sn39.1-15"


def test_sutta_info_s_4nt_link_sn_peyyala_range_override() -> None:
    su = SuttaInfo()
    su.sc_code = "SN23.23"

    assert su.s_4nt_link == "https://s.4nt.org/sn/sn23/index.html#sn23.23-33"


def test_sutta_info_s_4nt_link_an_peyyala_range_override() -> None:
    su = SuttaInfo()
    su.sc_code = "AN3.156"

    assert su.s_4nt_link == "https://s.4nt.org/an/an3/index.html#an3.156-162"


def test_sutta_info_s_4nt_link_dhp_vagga_range_override_anchors_first_verse() -> None:
    su = SuttaInfo()
    su.sc_code = "DHP90-00"

    assert su.s_4nt_link == "https://s.4nt.org/kn/dhp/index.html#dhp90"


def test_sutta_info_s_4nt_link_kn_books_link_to_exact_sutta_anchor() -> None:
    for sc_code, expected_book in [
        ("KP1", "kp"),
        ("UD1.1", "ud"),
        ("ITI1", "iti"),
        ("SNP1.1", "snp"),
        ("THAG1.1", "thag"),
        ("THIG1.1", "thig"),
        ("JA1", "ja"),
    ]:
        su = SuttaInfo()
        su.sc_code = sc_code
        assert (
            su.s_4nt_link
            == f"https://s.4nt.org/kn/{expected_book}/index.html#{sc_code.lower()}"
        )


def test_sutta_info_s_4nt_link_none_for_unknown_book() -> None:
    su = SuttaInfo()
    su.sc_code = "VIN1"

    assert su.s_4nt_link is None


def test_sutta_info_s_4nt_link_none_without_sc_code() -> None:
    su = SuttaInfo()

    assert su.s_4nt_link is None
