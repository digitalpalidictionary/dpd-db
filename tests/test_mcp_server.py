import json
from exporter.mcp.server import get_grammatical_details

def test_get_grammatical_details_response_format():
    sentence = "Evaṃ me sutaṃ."
    response_json = get_grammatical_details(sentence)
    
    # Verify it's a valid JSON string
    data = json.loads(response_json)
    assert isinstance(data, list)
    assert len(data) == 3
    
    for item in data:
        assert "word" in item
        assert "status" in item
        assert "details" in item
        if item["status"] == "found":
            assert len(item["details"]) > 0
            detail = item["details"][0]
            assert "lemma_1" in detail
            assert "pos" in detail
            assert "grammar" in detail
            assert "meaning_combo" in detail
            assert "family_root" in detail

def test_get_grammatical_details_not_found():
    sentence = "abbcccddd"
    response_json = get_grammatical_details(sentence)
    data = json.loads(response_json)
    
    assert data[0]["word"] == "abbcccddd"
    assert data[0]["status"] == "not_found"
    assert data[0]["details"] == []
