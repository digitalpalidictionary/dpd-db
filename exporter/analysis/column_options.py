"""CSV column registry and presets for export_words_csv.py.

To use a custom column set, edit the CUSTOM list below. Available keys are
all entries in REGISTRY. The 'example', 'source', and 'sutta' columns are
always populated from passage context, not the DB extractor.
"""

import re
from collections.abc import Callable

from db.models import DpdHeadword


def _root(hw: DpdHeadword) -> str:
    if hw.rt is None:
        return ""
    return re.sub(r" \d*$", "", str(hw.root_key))


REGISTRY: dict[str, Callable[[DpdHeadword], str]] = {
    "id": lambda hw: str(hw.id),
    "lemma_1": lambda hw: hw.lemma_1 or "",
    "pali": lambda hw: hw.lemma_1 or "",
    "grammar": lambda hw: hw.grammar or "",
    "neg": lambda hw: hw.neg or "",
    "verb": lambda hw: hw.verb or "",
    "trans": lambda hw: hw.trans or "",
    "plus_case": lambda hw: hw.plus_case or "",
    "meaning_combo": lambda hw: hw.meaning_combo or "",
    "meaning_lit": lambda hw: hw.meaning_lit or "",
    "sanskrit": lambda hw: hw.sanskrit or "",
    "sanskrit_root": lambda hw: hw.rt.sanskrit_root if hw.rt else "",
    "sanskrit_root_meaning": lambda hw: hw.rt.sanskrit_root_meaning if hw.rt else "",
    "sanskrit_root_class": lambda hw: hw.rt.sanskrit_root_class if hw.rt else "",
    "root": _root,
    "root_has_verb": lambda hw: hw.rt.root_has_verb if hw.rt else "",
    "root_group": lambda hw: str(hw.rt.root_group) if hw.rt else "",
    "root_sign": lambda hw: hw.root_sign or "",
    "root_meaning": lambda hw: hw.rt.root_meaning if hw.rt else "",
    "root_base": lambda hw: hw.root_base or "",
    "construction": lambda hw: (hw.construction or "").replace("\n", "<br>"),
    "derivative": lambda hw: hw.derivative or "",
    "suffix": lambda hw: hw.suffix or "",
    "phonetic": lambda hw: (hw.phonetic or "").replace("\n", "<br>"),
    "compound_type": lambda hw: hw.compound_type or "",
    "compound_construction": lambda hw: hw.compound_construction or "",
    # context columns — values injected by the writer
    "source": lambda _hw: "",
    "sutta": lambda _hw: "",
    "example": lambda _hw: "",
}

PRESETS: dict[str, list[str]] = {
    "basic": [
        "id",
        "lemma_1",
        "grammar",
        "meaning_combo",
        "source",
        "sutta",
        "example",
    ],
    "advanced": [
        "id",
        "pali",
        "grammar",
        "neg",
        "verb",
        "trans",
        "plus_case",
        "meaning_combo",
        "meaning_lit",
        "sanskrit",
        "sanskrit_root",
        "sanskrit_root_meaning",
        "sanskrit_root_class",
        "root",
        "root_has_verb",
        "root_group",
        "root_sign",
        "root_meaning",
        "root_base",
        "construction",
        "derivative",
        "suffix",
        "phonetic",
        "compound_type",
        "compound_construction",
        "source",
        "sutta",
        "example",
    ],
}

# Edit this list to create your own column set (choose from REGISTRY keys above).
CUSTOM: list[str] = list(PRESETS["basic"])
