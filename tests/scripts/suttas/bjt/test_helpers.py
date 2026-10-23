"""Tests for scripts/suttas/bjt/helpers.py, using real BJT heading strings."""

import pytest

from scripts.suttas.bjt.helpers import clean_string


@pytest.mark.parametrize(
    ("heading", "expected"),
    [
        # trailing full stop (an-1.json)
        ("5. sūkavaggo.", "5. sūkavaggo"),
        ("1. 10. 21-30.", "1. 10. 21-30"),
        # square brackets (an-1.json)
        ("[1. paṭhamovaggo]", "1. paṭhamovaggo"),
        # footnote marker inside brackets (an-1.json)
        ("[6. accharāsaṅghātavaggo{*}]", "6. accharāsaṅghātavaggo"),
        # footnote marker outside brackets (an-3-3.json)
        ("[3. bharaṇḍu vaggo]{*}", "3. bharaṇḍu vaggo"),
        # footnote marker, no brackets (an-11.json)
        ("paṭhama saññā suttaṃ{*}", "paṭhama saññā suttaṃ"),
        # round brackets (an-4-2.json)
        ("[paṭhama (nakula) samajīvīsuttaṃ]", "paṭhama nakula samajīvīsuttaṃ"),
        # round brackets plus footnote marker (an-4-2.json)
        ("[ahi (metta) suttaṃ]{*}", "ahi metta suttaṃ"),
    ],
)
def test_clean_string(heading: str, expected: str) -> None:
    assert clean_string(heading) == expected
