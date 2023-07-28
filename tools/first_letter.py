"""Finds the first Pāḷi letter, including aspirates like ch jh etc."""

from tools.pali_alphabet import pali_alphabet


def find_first_letter(word: str) -> str:
    """Find the first letter, including aspirated double letters ch jh etc."""
    if len(word) > 1:
        if word[:2] in pali_alphabet:
            return word[:2]
        else:
            return word[0]
    else:
        return word[0]
