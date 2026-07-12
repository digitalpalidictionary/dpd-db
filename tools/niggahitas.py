"""Add all variants of niggahita character (ŋ ṁ) to a list."""


def add_niggahitas(words: list[str], all: bool = True) -> list[str]:
    """Add various types of niggahitas (ŋ ṁ) to a list."""

    for word in words:
        if "ṃ" in word:
            words += [word.replace("ṃ", "ṁ")]
            if all:
                words += [word.replace("ṃ", "ŋ")]

    return list(set(words))
