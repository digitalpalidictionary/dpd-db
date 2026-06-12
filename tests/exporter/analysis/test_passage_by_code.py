"""Verify CST passage retrieval by canonical sutta code."""

from bs4 import BeautifulSoup

import exporter.analysis.passage_by_code as passage_by_code


def test_get_passage_by_code_matches_lowercase_prose_code(monkeypatch) -> None:
    def fake_find_prose_paragraphs(
        book: str, source_code: str
    ) -> tuple[str, list[str]]:
        assert book == "an3"
        assert source_code == "AN3.12"
        return "sāraṇīyasutta", ["Sāraṇīyāni bhikkhave dhammā."]

    monkeypatch.setattr(
        passage_by_code,
        "_find_prose_paragraphs",
        fake_find_prose_paragraphs,
    )

    result = passage_by_code.get_passage_by_code("an3.12")

    assert result.source == "AN3.12"
    assert result.vagga == "sāraṇīyasutta"
    assert result.paragraphs == ["Sāraṇīyāni bhikkhave dhammā."]
    assert result.is_verse is False


def test_get_passage_by_code_matches_spaced_prose_code(monkeypatch) -> None:
    def fake_find_prose_paragraphs(
        book: str, source_code: str
    ) -> tuple[str, list[str]]:
        assert book == "sn1"
        assert source_code == "SN35.1"
        return "saḷāyatanavagga", ["Evaṃ me sutaṃ."]

    monkeypatch.setattr(
        passage_by_code,
        "_find_prose_paragraphs",
        fake_find_prose_paragraphs,
    )

    result = passage_by_code.get_passage_by_code("sn 35.1")

    assert result.source == "SN35.1"
    assert result.vagga == "saḷāyatanavagga"
    assert result.paragraphs == ["Evaṃ me sutaṃ."]
    assert result.is_verse is False


def test_get_passage_by_code_keeps_opening_prose_sentences(monkeypatch) -> None:
    def fake_find_prose_paragraphs(
        book: str, source_code: str
    ) -> tuple[str, list[str]]:
        assert book == "an3"
        assert source_code == "AN3.12"
        return (
            "rathakāravaggo, sāraṇīyasuttaṃ",
            [
                (
                    "tīṇimāni, bhikkhave, rañño khattiyassa muddhāvasittassa "
                    "yāvajīvaṃ sāraṇīyāni bhavanti. katamāni tīṇi? "
                    "yasmiṃ, bhikkhave, padese rājā khattiyo muddhāvasitto "
                    "jāto hoti."
                )
            ],
        )

    monkeypatch.setattr(
        passage_by_code,
        "_find_prose_paragraphs",
        fake_find_prose_paragraphs,
    )

    result = passage_by_code.get_passage_by_code("AN3.12")

    assert result.paragraphs[0].startswith("tīṇ'imāni, bhikkhave")
    assert "katamāni tīṇi?" in result.paragraphs[0]


def test_clean_prose_paragraph_removes_cst_number() -> None:
    paragraph = passage_by_code._clean_prose_paragraph(
        "12. tīṇimāni, bhikkhave, rañño khattiyassa."
    )

    assert paragraph == "tīṇimāni, bhikkhave, rañño khattiyassa."


def test_find_prose_paragraphs_excludes_next_sutta_title(monkeypatch) -> None:
    soup = BeautifulSoup(
        """
        <root>
            <head rend="chapter">1. Rathakāravaggo</head>
            <p rend="subhead">12. Sāraṇīyasuttaṃ</p>
            <p rend="bodytext" n="12">12. tīṇimāni, bhikkhave.</p>
            <p rend="bodytext">puna caparaṃ, bhikkhave.</p>
            <p rend="subhead">13. Āsaṃsasuttaṃ</p>
        </root>
        """,
        "xml",
    )

    class FakeGlobalData:
        def __init__(self, book: str, text_to_find: str) -> None:
            self.book = book
            self.text_to_find = text_to_find
            self.soups = [soup]
            self.x = None
            self.source = ""
            self.sutta = ""
            self.vagga = ""
            self.samyutta = ""
            self.vagga_counter = 0
            self.sutta_counter = 0
            self.samyutta_counter = 0

        @property
        def sutta_clean(self) -> str:
            return self.sutta.split(",", 1)[0]

    monkeypatch.setattr(passage_by_code, "GlobalData", FakeGlobalData)

    vagga, paragraphs = passage_by_code._find_prose_paragraphs("an3", "AN3.12")

    assert vagga == "rathakāravaggo, sāraṇīyasuttaṃ"
    assert paragraphs == [
        "tīṇimāni, bhikkhave.",
        "puna caparaṃ, bhikkhave.",
    ]


def test_find_prose_paragraphs_keeps_mixed_blocks_in_source_order(monkeypatch) -> None:
    soup = BeautifulSoup(
        """
        <root>
            <head rend="chapter">Brahmasaṃyuttaṃ</head>
            <p rend="subhead">1. Brahmāyācanasuttaṃ</p>
            <p rend="bodytext" n="1">evaṃ me sutaṃ.</p>
            <p rend="gatha1">‘appeva nāma satthā dhammaṃ deseyyā’ti.</p>
            <p rend="bodytext">itiha bhagavato paṭisañcikkhato appossukkatāya cittaṃ namati.</p>
        </root>
        """,
        "xml",
    )

    class FakeGlobalData:
        def __init__(self, book: str, text_to_find: str) -> None:
            self.book = book
            self.text_to_find = text_to_find
            self.soups = [soup]
            self.x = None
            self.source = ""
            self.sutta = ""

    def fake_sn_formatter(g) -> None:
        text = g.x.text.strip()
        if text in {
            "evaṃ me sutaṃ.",
            "‘appeva nāma satthā dhammaṃ deseyyā’ti.",
            "itiha bhagavato paṭisañcikkhato appossukkatāya cittaṃ namati.",
        }:
            g.source = "SN6.1"
            g.sutta = "brahmasaṃyuttaṃ, brahmāyācanasuttaṃ"
        else:
            g.source = ""
            g.sutta = ""

    monkeypatch.setattr(passage_by_code, "GlobalData", FakeGlobalData)
    monkeypatch.setitem(
        passage_by_code.PROSE_FORMATTERS,
        "SN",
        fake_sn_formatter,
    )

    vagga, paragraphs = passage_by_code._find_prose_paragraphs("sn1", "SN6.1")

    assert vagga == "brahmasaṃyuttaṃ, brahmāyācanasuttaṃ"
    assert paragraphs == [
        "evaṃ me sutaṃ.",
        "appeva nāma satthā dhammaṃ deseyyāti.",
        "itiha bhagavato paṭisañcikkhato appossukkatāya cittaṃ namati.",
    ]
