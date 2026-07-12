"""Tests for tools/degree_of_completion.py word completeness symbol."""

from db.models import DpdHeadword
from tools.degree_of_completion import degree_of_completion


def test_complete_html() -> None:
    i = DpdHeadword(meaning_1="x", source_1="dn1")
    assert degree_of_completion(i) == """<span class="gray">✔</span>"""


def test_complete_plain() -> None:
    i = DpdHeadword(meaning_1="x", source_1="dn1")
    assert degree_of_completion(i, html=False) == "✔"


def test_half_complete_html() -> None:
    i = DpdHeadword(meaning_1="x", source_1="")
    assert degree_of_completion(i) == """<span class="gray">◑</span>"""


def test_half_complete_plain() -> None:
    i = DpdHeadword(meaning_1="x", source_1="")
    assert degree_of_completion(i, html=False) == "◑"


def test_incomplete_html() -> None:
    i = DpdHeadword(meaning_1="", source_1="")
    assert degree_of_completion(i) == """<span class="gray">✘</span>"""


def test_incomplete_plain() -> None:
    i = DpdHeadword(meaning_1="", source_1="")
    assert degree_of_completion(i, html=False) == "✘"
