#!/usr/bin/env python3

"""Function to provide traditional lemma endings."""

import re
from db.models import DpdHeadword
from tools.sinhala_tools import translit_ro_to_si

lemma_trad_dict: dict[str, str] = {
    "ant adj": "antu",          # like sīlavant
    "ant masc": "antu",         # like bhagavant
    "ar fem": "u",              # like dhītar
    "ar masc": "u",             # like satthar
    "ar2 masc": "u",            # like pitar
    "arahant masc": "arahanta", # like arahant
    "as masc": "a",             # like manas
    "bhavant masc": "bhavantu", # like bhavant
}

def find_space_digits(i: DpdHeadword) -> str:
    pattern = r"\s\d.*"
    match = re.search(pattern, i.lemma_1)
    if match:
        return match.group()
    else:
        return ""

def make_lemma_trad(i: DpdHeadword) -> str:
    """Return a traditional noun or adj ending, rather than the DPD ending."""

    if (
        "!" not in i.stem   # only process lemmas, not inflected forms
        and i.pattern in lemma_trad_dict
    ):
        space_digits = find_space_digits(i)
        ending = lemma_trad_dict[i.pattern]
        lemma_trad = f"{i.stem}{ending}{space_digits}" \
            .replace("!", "") \
            .replace("*", "")
        # print(f"{i.lemma_1:<40}{lemma_trad}")
        return lemma_trad
    else:
        return i.lemma_1


def make_lemma_trad_si(i: DpdHeadword) -> str:
    """Transcribe traditional lemma into Sinhala."""
    lemma = make_lemma_trad(i)
    return translit_ro_to_si(lemma)
