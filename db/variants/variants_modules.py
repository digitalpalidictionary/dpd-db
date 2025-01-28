from typing import TypeAlias

from tools.pali_alphabet import pali_alphabet

VariantsDict: TypeAlias = dict[str, dict[str, dict[str, list[str]]]]


def key_cleaner(key: str) -> str:
    """Remove non-Pāḷi characters from the key"""
    
    key_clean: str = ''.join(c for c in key.lower() if c in pali_alphabet)
    key_clean = key_clean.lower()
    return key_clean