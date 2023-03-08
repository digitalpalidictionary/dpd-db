

def add_niggahitas(synonyms: list) -> list:
    """add various types of niggahitas to synonyms"""
    for synonym in synonyms:
        if "ṃ" in synonym:
            synonyms += [synonym.replace("ṃ", "ṁ")]
            synonyms += [synonym.replace("ṃ", "ŋ")]
    return synonyms
