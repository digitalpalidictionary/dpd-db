from typing import List

from fuzzywuzzy import process as fuzzy_process


def find_closest_matches(
    term: str, allowed_list: List[str], limit: int = 3
) -> List[str]:
    """Finds the closest matches for a term within a list of allowed strings.

    Args:
        term: The input term to match.
        allowed_list: The list of valid strings to match against.
        limit: The maximum number of suggestions to return.

    Returns:
        A list of the closest matching strings from allowed_list.
    """
    if not allowed_list or not term:
        return []

    # extractBests returns tuples of (match, score)
    matches = fuzzy_process.extractBests(term, allowed_list, limit=limit)

    # Return only the matched strings (the first element of each tuple)
    return [match[0] for match in matches]
