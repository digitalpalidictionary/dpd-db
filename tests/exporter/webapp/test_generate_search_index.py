from exporter.webapp.generate_search_index import strip_diacritics, build_index


def test_strip_diacritics():
    assert strip_diacritics("bhū") == "bhu"
    assert strip_diacritics("√bhū") == "bhu"
    assert strip_diacritics("rūpa") == "rupa"
    assert strip_diacritics("ñāṇa") == "nana"
    assert strip_diacritics("Pāḷi") == "Pali"


def test_build_index():
    terms = {"bhū", "bhu", "rūpa", "rupa"}
    expected = ["bhu|bhu|bhū", "rupa|rupa|rūpa"]
    assert build_index(terms) == expected


def test_build_index_sorting():
    # Test alphabetical order of primary keys
    terms = {"rūpa", "bhū", "bhu"}
    index = build_index(terms)
    assert index[0] == "bhu|bhu|bhū"
    assert index[1] == "rupa|rūpa"
