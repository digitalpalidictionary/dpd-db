import re
from scripts.extractor._normalize import normalize_headword

def extract_cpd_headwords(cpd_data: list) -> set[str]:
    """Extract normalized headwords from CPD data."""
    headwords = set()
    for entry in cpd_data:
        if isinstance(entry, list) and len(entry) >= 1:
            headword = entry[0]
            # Normalize for comparison
            normalized = normalize_headword(headword)
            headwords.add(normalized)
    return headwords

def get_cpd_html_entries(cpd_data: list, word: str) -> list[tuple[str, str]]:
    """Get all CPD HTML entries for a word (handles homonyms).

    Returns list of tuples: (homonym_number, html)
    Extracts homonym number from <sup>N</sup> tag in HTML.
    """
    entries = []
    # The word from the list is already normalized
    target = word.lower()
    
    for entry in cpd_data:
        if isinstance(entry, list) and len(entry) >= 2:
            # Strip leading digits and normalize the headword in CPD source
            clean_headword = re.sub(r"^\d+", "", entry[0])
            normalized_headword = normalize_headword(clean_headword)
            
            if normalized_headword == target:
                html = entry[1]
                # Extract homonym number from <sup>N</sup>
                match = re.search(r"<sup>(\d+)</sup>", html)
                homonym = match.group(1) if match else "1"
                entries.append((homonym, html))

    # Sort by homonym number
    entries.sort(key=lambda x: int(x[0]))
    return entries
