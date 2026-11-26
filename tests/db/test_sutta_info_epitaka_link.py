"""SuttaInfo.epitaka_link: the link that opens a sutta in the ePitaka app.

The rows are copied from `sutta_info` in dpd.db.
"""

from db.models import SuttaInfo


def _row(
    dpd_code: str,
    dpd_sutta: str,
    sc_code: str,
    dpd_sutta_var: str = "",
    cst_vagga: str = "",
    sc_vagga: str = "",
    bjt_vagga: str = "",
) -> SuttaInfo:
    su = SuttaInfo()
    su.dpd_code = dpd_code
    su.dpd_sutta = dpd_sutta
    su.dpd_sutta_var = dpd_sutta_var
    su.sc_code = sc_code
    su.cst_vagga = cst_vagga
    su.sc_vagga = sc_vagga
    su.bjt_vagga = bjt_vagga
    return su


def test_a_sutta_links_by_its_suttacentral_code_in_lower_case() -> None:
    su = _row(
        "AN4.126",
        "dutiyamettāsutta",
        "AN4.126",
        cst_vagga="3. Bhayavaggo",
        sc_vagga="13. Bhayavagga",
        bjt_vagga="2. kesivaggo",
    )
    assert su.epitaka_link == "epitaka://sutta?code=an4.126"
    assert su.epitaka_web_link == "https://epitaka.org/app/sutta?code=an4.126"


def test_a_group_page_has_no_web_link_either() -> None:
    su = _row("SN1", "devatāsaṃyutta", "SN1.1", cst_vagga="1. Naḷavaggo")
    assert su.epitaka_web_link is None


def test_the_suttacentral_code_wins_over_the_dpd_code() -> None:
    su = _row(
        "TH1",
        "subhūtittheragāthā",
        "THAG1.1",
        cst_vagga="1. Paṭhamavaggo",
        sc_vagga="Ekakanipāta, Paṭhamavagga",
        bjt_vagga="4. mahāvaggo",
    )
    assert su.epitaka_link == "epitaka://sutta?code=thag1.1"


def test_the_dpd_code_is_used_when_there_is_no_suttacentral_code() -> None:
    su = _row(
        "SN46.36",
        "yonisomanasikārasutta",
        "",
        cst_vagga="4. Nīvaraṇavaggo",
    )
    assert su.epitaka_link == "epitaka://sutta?code=sn46.36"


def test_a_samyutta_has_no_link() -> None:
    su = _row(
        "SN1",
        "devatāsaṃyutta",
        "SN1.1",
        cst_vagga="1. Naḷavaggo",
        sc_vagga="1. Naḷavagga",
        bjt_vagga="1. naḷavaggo",
    )
    assert su.epitaka_link is None


def test_a_pannasaka_has_no_link() -> None:
    su = _row(
        "MN1-50",
        "mūlapaṇṇāsapāḷi",
        "MN1",
        dpd_sutta_var="mūlapaṇṇāsaka 1",
        cst_vagga="1. Mūlapariyāyavaggo",
        sc_vagga="Mūlapariyāyavagga",
        bjt_vagga="1. mūlapariyāyavaggo",
    )
    assert su.epitaka_link is None


def test_a_nipata_has_no_link() -> None:
    su = _row("AN1", "ekakanipātapāḷi", "AN1")
    assert su.epitaka_link is None


def test_a_vagga_has_no_link() -> None:
    su = _row("AN8.1-10", "mettāvagga", "AN8.10", sc_vagga="1. Mettāvagga")
    assert su.epitaka_link is None


def test_a_row_with_no_code_has_no_link() -> None:
    su = _row("", "brahmajālasutta", "")
    assert su.epitaka_link is None
