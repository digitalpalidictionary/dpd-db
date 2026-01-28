import pytest
from exporter.webapp.generate_search_index import strip_diacritics, build_index

def test_strip_diacritics():
    assert strip_diacritics("bhū") == "bhu"
    assert strip_diacritics("√bhū") == "bhu"
    assert strip_diacritics("rūpa") == "rupa"
    assert strip_diacritics("ñāṇa") == "nana"
    assert strip_diacritics("Pāḷi") == "Pali"

def test_build_index():
    terms = ["bhū", "bhu", "rūpa", "rupa"]
    expected = {
        "bhu": ["bhu", "bhū"],
        "rupa": ["rupa", "rūpa"]
    }
    assert build_index(terms) == expected

def test_build_index_sorting():
    # We might want the terms to be sorted in the list
    terms = ["bhu", "bhū"]
    index = build_index(terms)
    assert index["bhu"] == ["bhu", "bhū"]
