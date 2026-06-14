"""Unit tests for individual ``tools.cst_source`` book parsers.

These drive a single parser instance with hand-built chunks, so they are fast
(no CST XML parsing) and pin down the source/sutta values the GUI persists onto
headwords.
"""

import pytest
from bs4 import BeautifulSoup, element
from bs4.element import Tag

from tools.cst_source.loader import make_cst_soup
from tools.cst_source.parsers.abhidhamma import Abh2Parser
from tools.cst_source.parsers.khuddaka import Kn17Parser
from tools.cst_source.parsers.misc import ApParser, AptParser
from tools.cst_source.text_utils import get_text_and_number
from tools.paths import ProjectPaths

# Subheads Kn17Parser deliberately skips (copied verbatim from the parser).
_KN17_EXCLUDED_SUBHEADS = [
    "Paṭhamacchakkaṃ",
    "Dutiyacchakkaṃ",
    "Tatiyacchakkaṃ",
    "Paṭhamacatukkaniddeso",
    "Dutiyacatukkaniddeso",
    "Tatiyacatukkaniddeso",
    "Catutthacatukkaniddeso",
    "Ka. assādaniddeso",
    "Kha. ādīnavaniddeso",
    "Ga. nissaraṇaniddeso",
    "Ka. pabhedagaṇananiddeso",
    "Kha. cariyavāro",
    "Ga. cāravihāraniddeso",
    "Ka. ādhipateyyaṭṭhaniddeso",
    "Kha. ādivisodhanaṭṭhaniddeso",
    "Ga. adhimattaṭṭhaniddeso",
    "Gha. adhiṭṭhānaṭṭhaniddeso",
    "Ṅa. pariyādānaṭṭhaniddeso",
    "Ca. patiṭṭhāpakaṭṭhaniddeso",
    "Mūlamūlakādidasakaṃ",
    "Suttantaniddeso",
    "Dasaiddhiniddeso",
]


def _chunk(html: str) -> element.Tag:
    tag = BeautifulSoup(html, "html.parser").find(["head", "p"])
    assert isinstance(tag, element.Tag)
    return tag


def test_ap_emits_ap_prefix() -> None:
    """ap (Abhidhānappadīpikāpāṭha, the root text) must emit ``AP…`` — the
    registered book code in abbreviations.tsv. The old ``APP`` was bogus."""
    parser = ApParser("ap")

    parser.update(_chunk('<p rend="chapter">1. Saggakaṇḍa</p>'))
    assert parser.source == "AP1"

    parser.update(_chunk('<p rend="title">1. Bhūmivagga</p>'))
    assert parser.source.startswith("AP")
    assert not parser.source.startswith("APP")


def test_apt_emits_apt_prefix() -> None:
    """apt (Abhidhānappadīpikā Ṭīkā, the commentary) must emit ``APt…``,
    distinct from ap (``AP…``) — different books, different codes."""
    parser = AptParser("apt")

    parser.update(_chunk('<p rend="chapter">1. Saggakaṇḍavaṇṇanā</p>'))
    assert parser.source == "APt1"

    parser.update(_chunk('<p rend="title">2. Puravaggavaṇṇanā</p>'))
    assert parser.source.startswith("APt")


def test_abh2_vagga_less_subhead_uses_section() -> None:
    """A vagga-less abh2 subhead must fall back to ``{section}, {sutta}`` (mirroring
    Abh1Parser), not leak the old ``xxxxxxx`` debug placeholder."""
    parser = Abh2Parser("abh2")

    # chapter sets section and resets vagga to ""
    parser.update(_chunk('<p rend="chapter">1. Khandhavibhaṅgo</p>'))
    assert parser.vagga == ""

    # subhead before any title -> not self.vagga branch
    parser.update(_chunk('<p rend="subhead">1. Rūpakkhandho</p>'))
    assert "xxxxxxx" not in parser.sutta
    assert parser.sutta == "khandhavibhaṅgo, rūpakkhandho"


@pytest.mark.slow
def test_kn17_no_nameless_subhead_branch() -> None:
    """The removed Kn17Parser branch (``vagga and section and not sutta_name``)
    referenced unbound locals and could only ever raise. Parsing the real kn17
    XML must never hit that condition and must never raise — proving the deleted
    branch was genuinely dead code (copy-paste residue from a prior book)."""
    parser = Kn17Parser("kn17")
    dead_branch_condition_hits = 0

    for soup in make_cst_soup(ProjectPaths(), "kn17"):
        for x in soup.find_all(["head", "p"]):
            if not isinstance(x, Tag):
                continue
            if x.get("rend") == "subhead" and x.text not in _KN17_EXCLUDED_SUBHEADS:
                sutta_name, _ = get_text_and_number(x.text)
                if parser.vagga and parser.section and not sutta_name:
                    dead_branch_condition_hits += 1
            parser.update(x)  # would raise UnboundLocalError if the branch fired

    assert dead_branch_condition_hits == 0
