from exporter.mcp.analyzer import tokenize_sentence

def test_tokenize_sentence_basic():
    sentence = "Evaṃ me sutaṃ."
    tokens = tokenize_sentence(sentence)
    assert tokens == ["evaṃ", "me", "sutaṃ"]

def test_tokenize_sentence_punctuation():
    sentence = "Namo tassa bhagavato, arahato, sammāsambuddhassa!"
    tokens = tokenize_sentence(sentence)
    assert tokens == ["namo", "tassa", "bhagavato", "arahato", "sammāsambuddhassa"]

def test_tokenize_sentence_empty():
    assert tokenize_sentence("") == []
    assert tokenize_sentence("   ") == []

def test_analyze_sentence():
    # This test requires a valid dpd.db to be present at the expected path.
    from exporter.mcp.analyzer import analyze_sentence
    from db.db_helpers import get_db_session
    from exporter.mcp.config import mcp_config

    db_session = get_db_session(mcp_config.db_path)
    
    sentence = "Evaṃ me sutaṃ."
    results = analyze_sentence(sentence, db_session)
    
    assert len(results) == 3
    # Check "evaṃ"
    assert results[0]["word"] == "evaṃ"
    assert "lemma_1" in results[0]["details"][0]
    
    # Check "me"
    assert results[1]["word"] == "me"
    
    # Check "sutaṃ"
    assert results[2]["word"] == "sutaṃ"

def test_analyze_sentence_not_found():
    from exporter.mcp.analyzer import analyze_sentence
    from db.db_helpers import get_db_session
    from exporter.mcp.config import mcp_config

    db_session = get_db_session(mcp_config.db_path)
    
    # Using a string that is Pāḷi-alphabet-only but unlikely to be in the dictionary
    sentence = "abbcccddd"
    results = analyze_sentence(sentence, db_session)
    
    assert len(results) == 1
    assert results[0]["word"] == "abbcccddd"
    assert results[0]["status"] == "not_found"
