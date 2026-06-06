# -*- coding: utf-8 -*-
import json
import re
from pathlib import Path
from typing import TypeAlias

from tools.pali_alphabet import pali_alphabet

VariantsDict: TypeAlias = dict[str, dict[str, dict[str, list[tuple[str, str]]]]]

_CHAR_SET: frozenset[str] = frozenset([" ", *pali_alphabet])


def key_cleaner(key: str) -> str:
    """Remove non-Pāḷi characters from the key"""

    key_clean: str = "".join(c for c in key.lower() if c in _CHAR_SET)
    return key_clean


def context_cleaner(context: str) -> str:
    """Remove punctuation and digits from the context"""

    context = context.lower()
    context = context.replace("‘", "")  # single quote
    context = context.replace("“", "")  # double quote
    context = context.replace('"', "")  # double quote
    context = context.replace("(", "")  # left parenthesis
    context = context.replace(")", "")  # right parenthesis
    context = context.replace("*", "")  # asterisk
    context = re.sub(r"\d", "", context)  # digits
    context = re.sub(r"^\.", "", context)  # remove leading full stop
    context = re.sub(r"\.$", "", context)  # remove trailing full stop
    context = context.strip()

    return context


def save_json(variants_dict: VariantsDict) -> None:
    """Save variants to json"""

    with Path("temp/variants.json").open("w", encoding="utf-8") as f:
        json.dump(variants_dict, f, ensure_ascii=False, indent=2)
