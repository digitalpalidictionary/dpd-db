from db.lookup.transliterate_lookup_table import _should_transliterate
from db.models import Lookup


def make_lookup(
    lookup_key: str = "buddho", sinhala: str = "", **kwargs: object
) -> Lookup:
    row = Lookup()
    row.lookup_key = lookup_key
    row.sinhala = sinhala
    for k, v in kwargs.items():
        setattr(row, k, v)
    return row


def test_no_sinhala_non_epd_should_transliterate():
    """Row with no sinhala and real data (grammar) → transliterate."""
    row = make_lookup(sinhala="", grammar="verb")
    assert _should_transliterate(row, regenerate_all=False) is True


def test_has_sinhala_regenerate_non_epd_should_transliterate():
    """Row with sinhala, regenerate mode, real data → transliterate."""
    row = make_lookup(sinhala="බුද්ධො", grammar="verb")
    assert _should_transliterate(row, regenerate_all=True) is True


def test_has_sinhala_no_regenerate_skip():
    """Row with sinhala, not regenerating → skip."""
    row = make_lookup(sinhala="බුද්ධො", grammar="verb")
    assert _should_transliterate(row, regenerate_all=False) is False


def test_epd_only_skip_when_no_sinhala():
    """EPD-only row (no other data) → skip, even with no sinhala."""
    row = make_lookup(sinhala="")
    assert _should_transliterate(row, regenerate_all=False) is False


def test_epd_only_skip_even_with_regenerate():
    """EPD-only row → skip, even in regenerate mode."""
    row = make_lookup(sinhala="")
    assert _should_transliterate(row, regenerate_all=True) is False


def test_row_with_epd_plus_real_data_transliterate():
    """Row has epd data but also grammar (real data) → transliterate if no sinhala."""
    row = make_lookup(sinhala="", epd="Buddho", grammar="verb")
    assert _should_transliterate(row, regenerate_all=False) is True


def test_row_with_epd_plus_data_skip_when_has_sinhala():
    """Row has epd + grammar + sinhala, not regenerating → skip."""
    row = make_lookup(sinhala="බුද්ධො", epd="Buddho", grammar="verb")
    assert _should_transliterate(row, regenerate_all=False) is False
