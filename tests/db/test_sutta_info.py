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


def test_sutta_info_s_4nt_link_sn_links_to_samyutta_container() -> None:
    su = SuttaInfo()
    su.sc_code = "SN1.1"

    assert su.s_4nt_link == "https://s.4nt.org/sn/sn1/index.html"


def test_sutta_info_s_4nt_link_an_links_to_nipata_container() -> None:
    su = SuttaInfo()
    su.sc_code = "AN3.65"

    assert su.s_4nt_link == "https://s.4nt.org/an/an3/index.html"


def test_sutta_info_s_4nt_link_an_bare_nipata_code_links_to_own_container() -> None:
    su = SuttaInfo()
    su.sc_code = "AN5"

    assert su.s_4nt_link == "https://s.4nt.org/an/an5/index.html"


def test_sutta_info_s_4nt_link_range_code_has_clean_book_segment() -> None:
    su = SuttaInfo()
    su.sc_code = "SN39.1-15"

    assert su.s_4nt_link == "https://s.4nt.org/sn/sn39/index.html"


def test_sutta_info_s_4nt_link_kn_books_link_to_book_container() -> None:
    for sc_code, expected_book in [
        ("KP1", "kp"),
        ("DHP33-43", "dhp"),
        ("UD1.1", "ud"),
        ("ITI1", "iti"),
        ("SNP1.1", "snp"),
        ("THAG1.1", "thag"),
        ("THIG1.1", "thig"),
        ("JA1", "ja"),
    ]:
        su = SuttaInfo()
        su.sc_code = sc_code
        assert su.s_4nt_link == f"https://s.4nt.org/kn/{expected_book}/index.html"


def test_sutta_info_s_4nt_link_none_for_unknown_book() -> None:
    su = SuttaInfo()
    su.sc_code = "VIN1"

    assert su.s_4nt_link is None


def test_sutta_info_s_4nt_link_none_without_sc_code() -> None:
    su = SuttaInfo()

    assert su.s_4nt_link is None
