
import pytest
from exporter.mcp.analyzer import analyze_sentence
from db.db_helpers import get_db_session
from tools.paths import ProjectPaths

@pytest.fixture(scope="module")
def db_session():
    pth = ProjectPaths()
    session = get_db_session(pth.dpd_db_path)
    yield session
    session.close()

def test_analyze_simple_sentence(db_session):
    sentence = "buddho dhammaṃ deseti"
    results = analyze_sentence(sentence, db_session)
    
    assert len(results) == 3
    
    # Check 'buddho'
    buddho = results[0]
    assert buddho["word"] == "buddho"
    assert buddho["status"] == "found"
    # Allow case-insensitive lemma match and strip digits
    lemmas = [d["pali"].lower().split()[0] for d in buddho["data"]]
    assert "buddho" in lemmas, f"Expected 'buddho' in {lemmas}"
    # Check pos if available
    pos_list = [d["pos"] for d in buddho["data"]]
    assert "masc" in pos_list or "noun" in pos_list, f"Expected masc/noun in {pos_list}"

    # Check 'dhammaṃ'
    dhamma = results[1]
    assert dhamma["word"] == "dhammaṃ"
    assert dhamma["status"] == "found"
    lemmas = [d["pali"].lower().split()[0] for d in dhamma["data"]]
    assert "dhammaṃ" in lemmas, f"Expected 'dhammaṃ' in {lemmas}"

    # Check 'deseti'
    deseti = results[2]
    assert deseti["word"] == "deseti"
    assert deseti["status"] == "found"
    lemmas = [d["pali"].lower().split()[0] for d in deseti["data"]]
    assert "deseti" in lemmas, f"Expected 'deseti' in {lemmas}"

def test_analyze_sandhi(db_session):
    sentence = "yo'dha" # yo + idha
    results = analyze_sentence(sentence, db_session)
    
    assert len(results) == 1
    yodha = results[0]
    # With the fix, we expect the apostrophe to be preserved
    assert yodha["word"] == "yo'dha"
    assert yodha["status"] == "found"
    
    # Check decomposition
    found_split = False
    all_constructions = []
    for option in yodha["data"]:
        all_constructions.append(option.get("construction", ""))
        if "idha" in option.get("construction", "") and "yo" in option.get("construction", ""):
            found_split = True
            break
            
    assert found_split, f"Did not find construction 'yo + idha' in {all_constructions}"

def test_analyze_compound(db_session):
    sentence = "dhammacakkappavattana"
    results = analyze_sentence(sentence, db_session)
    
    assert len(results) == 1
    word = results[0]
    assert word["status"] == "found"
    
    # Check if components are resolved
    # We look for ANY option that breaks down into dhamma, cakka, pavattana
    # Note: dhammacakka might be a component itself.
    
    found_nested = False
    debug_info = []

    for option in word["data"]:
        if option["components"]:
            # Level 1 components
            l1_lemmas = []
            for comp_group in option["components"]:
                if comp_group:
                    # Each comp_group is a list of options for that component
                    # We assume the first option is the most relevant or we check all
                    l1_lemmas.append([x["pali"].lower().split()[0] for x in comp_group])
            
            debug_info.append(f"L1: {l1_lemmas}")
            
            # Check if we have (dhammacakka OR (dhamma AND cakka)) AND pavattana
            flat_l1 = [item for sublist in l1_lemmas for item in sublist]
            
            has_pavattana = "pavattana" in flat_l1
            has_dhammacakka = "dhammacakka" in flat_l1
            has_dhamma = "dhamma" in flat_l1
            has_cakka = "cakka" in flat_l1
            
            if has_pavattana and (has_dhammacakka or (has_dhamma and has_cakka)):
                found_nested = True
                
                # If we found dhammacakka, let's see if we can go deeper in that object
                # This requires that the 'dhammacakka' option inside 'components' has ITS OWN 'components'
                if has_dhammacakka:
                    # Find the dhammacakka object
                    for comp_group in option["components"]:
                        for comp_opt in comp_group:
                            if "dhammacakka" in comp_opt["pali"].lower():
                                # Check if this has components
                                if comp_opt.get("components"):
                                    # Check for dhamma and cakka inside
                                    l2_lemmas = []
                                    for l2_group in comp_opt["components"]:
                                        l2_lemmas.extend([x["pali"].lower().split()[0] for x in l2_group])
                                    if "dhamma" in l2_lemmas and "cakka" in l2_lemmas:
                                        # Full recursive success
                                        return 
    
    # If we are here, we might have found L1 but maybe not L2, or nothing.
    # The requirement is just to be "comprehensive", so if we found dhammacakka + pavattana, that's already good.
    # But ideally we want deep analysis.
    
    # Let's pass if we found at least dhammacakka + pavattana
    if found_nested:
        return

    pytest.fail(f"Did not find 'dhammacakka' + 'pavattana' (or deeper). Debug: {debug_info}")

def test_analyze_long_sentence(db_session):
    # From Dhammacakkappavattana Sutta
    sentence = "dve'me bhikkhave antā pabbajitena na sevitabbā"
    results = analyze_sentence(sentence, db_session)
    
    assert len(results) == 6
    
    # dve'me
    dveme = results[0]
    assert dveme["word"] == "dve'me"
    assert dveme["status"] == "found"
    
    # na
    na = results[4]
    assert na["word"] == "na"
    assert na["status"] == "found"
    lemmas = [d["pali"].lower().split()[0] for d in na["data"]]
    assert "na" in lemmas, f"Expected 'na' in {lemmas}"

if __name__ == "__main__":
    # verification runs
    pass
