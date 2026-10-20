"""Tests for the verse walk in ``tools.cst_source.examples``.

Fixtures are copied verbatim from the CST romn XML, so the verse markup is what
the corpus really holds (verses with no gatha1, verses with no gathalast).
"""

from bs4 import BeautifulSoup
from bs4.element import Tag

from tools.cst_source.examples import find_gatha_example, find_verse_start

# s0502m.mul.xml (Dhammapada), Dhp 1
DHP_1 = """
<p rend="hangnum" n="1"><hi rend="paranum">1</hi><hi rend="dot">.</hi></p>

<p rend="gatha1"> Manopubbaṅgamā <pb ed="M" n="0.0013" /><pb ed="V" n="0.0013" /><pb ed="P" n="0.0001" /><pb ed="T" n="0.0015" /> dhammā, manoseṭṭhā manomayā;</p>

<p rend="gatha2">Manasā ce paduṭṭhena, bhāsati vā karoti vā;</p>

<p rend="gathalast">Tato naṃ dukkhamanveti, cakkaṃva vahato padaṃ.</p>

<p rend="hangnum" n="2"><hi rend="paranum">2</hi><hi rend="dot">.</hi></p>
"""

# s0502m.mul.xml (Dhammapada), vaggānamuddānaṃ
DHP_VAGGA_UDDANA = """
<p rend="bodytext">Dhammapade vaggānamuddānaṃ –</p>

<p rend="gatha2">Yamakappamādo <pb ed="M" n="0.0075" /> cittaṃ, pupphaṃ bālena paṇḍito;</p>

<p rend="gathalast">Arahanto sahassañca, pāpaṃ daṇḍena te dasa.</p>

<p rend="gatha1">Jarā <pb ed="T" n="0.0072" /> attā ca loko ca, buddho sukhaṃ piyena ca;</p>

<p rend="gathalast">Kodho malañca dhammaṭṭho, maggavaggena vīsati.</p>

<p rend="gatha2">Pakiṇṇaṃ nirayo nāgo, taṇhā bhikkhu ca brāhmaṇo;</p>

<p rend="gathalast">Ete chabbīsati vaggā, desitādiccabandhunā.</p>

<p rend="bodytext">Gāthānamuddānaṃ –</p>
"""

# s0502m.mul.xml (Dhammapada), gāthānamuddānaṃ (first five verses)
DHP_GATHA_UDDANA = """
<p rend="bodytext">Gāthānamuddānaṃ –</p>

<p rend="gatha2">Yamake vīsati gāthā, appamādamhi dvādasa;</p>

<p rend="gathalast">Ekādasa cittavagge, pupphavaggamhi soḷasa.</p>

<p rend="gatha2">Bāle ca soḷasa gāthā, paṇḍitamhi catuddasa;</p>

<p rend="gathalast">Arahante dasa gāthā, sahasse honti soḷasa.</p>

<p rend="gatha2">Terasa pāpavaggamhi, daṇḍamhi dasa satta ca;</p>

<p rend="gathalast">Ekādasa jarā vagge, attavaggamhi tā dasa.</p>

<p rend="gatha2">Dvādasa <pb ed="M" n="0.0076" /><pb ed="V" n="0.0067" /> lokavaggamhi, buddhavaggamhi ṭhārasa <note>soḷasa (sabbattha)</note>;</p>

<p rend="gathalast">Sukhe ca piyavagge ca, gāthāyo honti dvādasa.</p>

<p rend="gatha2">Cuddasa kodhavaggamhi, malavaggekavīsati;</p>

<p rend="gathalast">Sattarasa ca dhammaṭṭhe, maggavagge sattarasa.</p>
"""

# s0506m.mul.xml (Vimānavatthu), VV10: a one-line verse with no gathalast
VV_10 = """
<p rend="gathalast">Pañhaṃ puṭṭhā viyākāsi, yassa kammassidaṃ phalaṃ.</p>

<p rend="hangnum" n="89"><hi rend="paranum">89</hi><hi rend="dot">.</hi></p>

<p rend="gatha1"> ‘Ahaṃ manussesu manussabhūtā, purimāya jātiyā manussaloke.</p>

<p rend="hangnum" n="90"><hi rend="paranum">90</hi><hi rend="dot">.</hi></p>

<p rend="gatha1"> ‘‘Addasaṃ virajaṃ buddhaṃ, vippasannamanāvilaṃ;</p>

<p rend="gatha2">Āsajja dānaṃ adāsiṃ, akāmā tiladakkhiṇaṃ;</p>

<p rend="gathalast">Dakkhiṇeyyassa buddhassa, pasannā sehi pāṇibhi.</p>
"""


# s0503m.mul.xml (Udāna), Ud 30: a six-line verse with a gatha1 on line five
UD_30 = """
<p rend="gathalast">Bhavataṇhā pahīyati, vibhavaṃ nābhinandati.</p>

<p rend="gatha1">‘‘Sabbaso taṇhānaṃ khayā,</p>

<p rend="gatha2">Asesavirāganirodho nibbānaṃ;</p>

<p rend="gatha3">Tassa nibbutassa bhikkhuno,</p>

<p rend="gatha2">Anupādā <note>anupādānā (sī.)</note> punabbhavo na hoti;</p>

<p rend="gatha1">Abhibhūto māro vijitasaṅgāmo,</p>

<p rend="gathalast">Upaccagā sabbabhavāni tādī’’ti. dasamaṃ;</p>

<trailer rend="centre">Nandavaggo tatiyo niṭṭhito.</trailer>
"""


# s0502m.mul.xml (Dhammapada), Dhp 99: the last verse of a vagga, with no gathalast
DHP_99 = """
<p rend="gatha1"> Ramaṇīyāni  araññāni, yattha na ramatī jano;</p>

<p rend="gatha2">Vītarāgā ramissanti, na te kāmagavesino.</p>

<trailer rend="centre">Arahantavaggo sattamo niṭṭhito.</trailer>
"""


# s0505a.att.xml (Dhammapada commentary): quotations, each a lone gathalast line
DHPA_QUOTES = """
<p rend="gathalast">‘‘Natthi rāgasamo aggi’’; (Dha. pa. 202);</p>

<p rend="gathalast">‘‘Kāmarāgena <pb ed="P" n="1.0017" /> dayhāmi, cittaṃ me paridayhati’’; (Saṃ. ni. 1.212);</p>

<p rend="gathalast">‘‘Ye rāgarattānupatanti sotaṃ, sayaṃ kataṃ makkaṭakova jālaṃ’’. (dha. pa. 347);</p>
"""


def parse(snippet: str) -> BeautifulSoup:
    """Parse ``snippet`` the way ``make_cst_soup`` prepares a book."""
    soup = BeautifulSoup(f"<div>{snippet}</div>", "xml")
    for pb in soup.find_all("pb"):
        pb.decompose()
    for note in soup.find_all("note"):
        note.replace_with(rf" [{note.text}] ")
    for hi in soup.find_all("hi", rend=["paranum", "dot"]):
        hi.unwrap()
    return soup


def find_line(soup: BeautifulSoup, starts_with: str) -> Tag:
    """Return the ``p`` whose text starts with ``starts_with``."""
    for p in soup.find_all("p"):
        if p.text.strip().lstrip("‘").startswith(starts_with):
            return p
    raise AssertionError(f"no line starting with {starts_with!r}")


def verse(snippet: str, starts_with: str) -> list[str]:
    return find_gatha_example(find_line(parse(snippet), starts_with))


def test_normal_verse_unchanged() -> None:
    assert verse(DHP_1, "Manasā") == [
        "manopubbaṅgamā dhammā,\nmanoseṭṭhā manomayā,\n"
        "manasā ce paduṭṭhena,\nbhāsati vā karoti vā,\n"
        "tato naṃ dukkhamanveti,\ncakkaṃva vahato padaṃ."
    ]


def test_verse_without_gatha1_after_heading() -> None:
    assert verse(DHP_GATHA_UDDANA, "Dvādasa") == [
        "dvādasa lokavaggamhi,\nbuddhavaggamhi ṭhārasa [soḷasa (sabbattha)],\n"
        "sukhe ca piyavagge ca,\ngāthāyo honti dvādasa."
    ]


def test_verse_without_gatha1_does_not_reach_earlier_verse() -> None:
    assert verse(DHP_VAGGA_UDDANA, "Pakiṇṇaṃ") == [
        "pakiṇṇaṃ nirayo nāgo,\ntaṇhā bhikkhu ca brāhmaṇo,\n"
        "ete chabbīsati vaggā,\ndesitādiccabandhunā."
    ]


def test_verse_without_gathalast_does_not_run_into_next_verse() -> None:
    assert verse(VV_10, "Ahaṃ") == [
        "ahaṃ manussesu manussabhūtā,\npurimāya jātiyā manussaloke."
    ]


def test_gatha1_inside_a_verse_does_not_end_it() -> None:
    assert verse(UD_30, "Sabbaso") == [
        "sabbaso taṇhānaṃ khayā,\nasesavirāganirodho nibbānaṃ,\n"
        "tassa nibbutassa bhikkhuno,\nanupādā [anupādānā] punabbhavo na hoti,\n"
        "abhibhūto māro vijitasaṅgāmo,\nupaccagā sabbabhavāni tādīti. dasamaṃ.\n"
    ]


def test_line_after_mid_verse_gatha1_starts_there() -> None:
    # The walk back stops at any gatha1, so lines 5-6 of Ud 30 stand alone.
    assert verse(UD_30, "Abhibhūto") == [
        "abhibhūto māro vijitasaṅgāmo,\nupaccagā sabbabhavāni tādīti. dasamaṃ.\n"
    ]


def test_verse_without_gathalast_ends_with_full_stop() -> None:
    assert verse(DHP_99, "Vītarāgā") == [
        "ramaṇīyāni araññāni,\nyattha na ramatī jano,\n"
        "vītarāgā ramissanti,\nna te kāmagavesino."
    ]


def test_verse_start_is_shared_by_its_lines_only() -> None:
    soup = parse(DHP_GATHA_UDDANA)
    first = find_line(soup, "Dvādasa")
    assert find_verse_start(first) is first
    assert find_verse_start(find_line(soup, "Sukhe")) is first
    assert find_verse_start(find_line(soup, "Cuddasa")) is not first


def test_single_line_verse_ends_with_full_stop() -> None:
    assert verse(DHPA_QUOTES, "Kāmarāgena") == [
        "kāmarāgena dayhāmi,\ncittaṃ me paridayhati,\n(saṃ. ni. 1.212).\n"
    ]
