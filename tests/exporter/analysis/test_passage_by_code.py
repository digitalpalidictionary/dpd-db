"""Verify CST passage retrieval by canonical sutta code."""

from bs4 import BeautifulSoup

from exporter.analysis import passage_by_code


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

    monkeypatch.setattr(passage_by_code, "make_cst_soup", lambda pth, book: [soup])

    # the real AnguttaraParser drives the "an3" book over the fake soup
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

    class FakeParser:
        def __init__(self) -> None:
            self.source = ""
            self.sutta = ""

        def update(self, x) -> None:
            text = x.text.strip()
            if text in {
                "evaṃ me sutaṃ.",
                "‘appeva nāma satthā dhammaṃ deseyyā’ti.",
                "itiha bhagavato paṭisañcikkhato appossukkatāya cittaṃ namati.",
            }:
                self.source = "SN6.1"
                self.sutta = "brahmasaṃyuttaṃ, brahmāyācanasuttaṃ"
            else:
                self.source = ""
                self.sutta = ""

    monkeypatch.setattr(passage_by_code, "make_cst_soup", lambda pth, book: [soup])
    monkeypatch.setattr(passage_by_code, "make_book_parser", lambda book: FakeParser())

    vagga, paragraphs = passage_by_code._find_prose_paragraphs("sn1", "SN6.1")

    assert vagga == "brahmasaṃyuttaṃ, brahmāyācanasuttaṃ"
    assert paragraphs == [
        "evaṃ me sutaṃ.",
        "appeva nāma satthā dhammaṃ deseyyāti.",
        "itiha bhagavato paṭisañcikkhato appossukkatāya cittaṃ namati.",
    ]
