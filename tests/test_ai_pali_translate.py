from scripts.ai_pali_translate import build_system_prompt

def test_build_system_prompt():
    analysis = [
        {
            "word": "evaṃ",
            "status": "found",
            "details": [
                {
                    "lemma_1": "evaṃ 1",
                    "pos": "ind",
                    "grammar": "ind, adv",
                    "meaning_combo": "thus",
                    "family_root": ""
                }
            ]
        }
    ]
    
    prompt = build_system_prompt(analysis)
    
    assert "expert Pāḷi translator" in prompt
    assert "evaṃ" in prompt
    assert "thus" in prompt
    assert "### Instructions:" in prompt
