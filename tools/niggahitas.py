"""Add all variants of niggahita character (ŋ ṁ) to a list."""

from typing import List

def add_niggahitas(words: List[str]) -> List[str]:
    """Add various types of niggahitas (ŋ ṁ) to a list."""

    for word in words:
        if "ṃ" in word:
            words += [word.replace("ṃ", "ṁ")]
            words += [word.replace("ṃ", "ŋ")]

    return words
