import re
from scripts.extractor._normalize import normalize_headword


def extract_cone_headwords(cone_dict: dict) -> set[str]:
    """Extract normalized headwords from Cone dictionary keys."""
    headwords = set()
    for key in cone_dict.keys():
        # Strip leading digits from key (e.g., "1a" -> "a", "2aṃsa" -> "aṃsa")
        clean_key = re.sub(r"^\d+", "", key)
        # Normalize for comparison
        normalized = normalize_headword(clean_key)
        headwords.add(normalized)
    return headwords


def get_cone_html_entries(cone_dict: dict, word: str) -> list[tuple[str, str]]:
    """Get all Cone HTML entries for a word (handles homonyms like 1abbeti, 2abbeti).

    Returns list of tuples: (homonym_number, html)
    """
    entries = []
    # The word from the list is already normalized
    target = word.lower()

    for key in cone_dict.keys():
        # Strip leading digits and normalize the dictionary key
        clean_key = re.sub(r"^\d+", "", key)
        normalized_key = normalize_headword(clean_key)

        if normalized_key == target:
            # Extract homonym number if present
            match = re.match(r"^(\d+)", key)
            homonym = match.group(1) if match else "1"
            entries.append((homonym, cone_dict[key]))

    # Sort by homonym number
    entries.sort(key=lambda x: int(x[0]))
    return entries
