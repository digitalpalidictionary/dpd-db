"""Add all variants of niggahita character (ŋ ṁ) to a list."""

from typing import List

def add_niggahitas(words: List[str], all=True) -> List[str]:
    """Add various types of niggahitas (ŋ ṁ) to a list."""

    for word in words:
        if "ṃ" in word:
            words += [word.replace("ṃ", "ṁ")]
            if all == True:
                words += [word.replace("ṃ", "ŋ")]

    return list(set(words))
