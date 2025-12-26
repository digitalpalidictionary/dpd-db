from exporter.mcp.ai_pali_translate import build_system_prompt

def test_build_system_prompt():
    analysis = [
        {
            "word": "cakkavattī",
            "status": "found",
            "deconstructor": [],
            "details": [
                {
                    "id": 25702,
                    "lemma_1": "cakkavattī",
                    "pos": "masc",
                    "grammar": "masc, agent, comp",
                    "meaning_combo": "emperor",
                    "construction": "cakka + vattī"
                }
            ],
            "components": {
                "cakka": [
                    {
                        "id": 25671,
                        "lemma_1": "cakka 1",
                        "pos": "nt",
                        "grammar": "nt",
                        "meaning_combo": "wheel"
                    }
                ]
            }
        }
    ]
    examples = "Examples placeholder"
    
    prompt = build_system_prompt(analysis, examples)
    
    assert "expert Pāḷi translator" in prompt
    assert "cakkavattī" in prompt
    assert "emperor" in prompt
    assert "cakka" in prompt
    assert "wheel" in prompt
    assert "### Instructions:" in prompt
    assert "components" in prompt
    assert "new row" in prompt
    assert "- mahā" in prompt
    assert "prefixed with a hyphen" in prompt
