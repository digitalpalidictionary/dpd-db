"""Remove all Pāḷi diacritics from a string and return standard
Roman alphabet text."""


def diacritics_cleaner(text: str) -> str:
    """Remove Pāḷi diacritics from a string."""
    return (
        text.replace("ā", "a")
        .replace("ī", "i")
        .replace("ū", "u")
        .replace("ṅ", "n")
        .replace("ñ", "n")
        .replace("ṇ", "n")
        .replace("ṭ", "t")
        .replace("ḍ", "d")
        .replace("ḷ", "l")
        .replace("ṃ", "m")
    )


# print(diacritics_cleaner("ṭhāṇa"))
