import re

def normalize_headword(word: str) -> str:
    """Normalize a headword for comparison.

    Applies combined DPD-style normalization rules:
    - ṁ → ṃ (normalize nasal m)
    - -in endings → -ī (agent nouns)
    - -at endings → -anta (present participles, but not -ati, -anta, -māna)
    - -an endings (masc) → -a
    """
    # Normalize ṁ to ṃ first
    word = word.replace("ṁ", "ṃ")
    word_lower = word.lower()

    # Agent nouns: -in → -ī
    if re.search(r"in$", word_lower):
        return word[:-2] + "ī"

    # Present participles: -at → -anta (but not -ati, -anta, -māna)
    if re.search(r"at$", word_lower) and not re.search(r"(ati|anta|māna)$", word_lower):
        return word[:-2] + "anta"

    # Masc nouns: -an → -a
    if re.search(r"an$", word_lower):
        return word[:-2] + "a"

    return word_lower
