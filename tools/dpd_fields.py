import re

from tools.pos import INDECLINABLES


def lemma_clean(lemma_1: str):
    return re.sub(r" \d.+", "", lemma_1)


def root_clean(root_key: str):
    return re.sub(r" \d.*", "", root_key)


def find_stem_pattern(pos: str, grammar: str, lemma_1: str):
    lemma_1_clean = lemma_clean(lemma_1)

    stem = ""
    pattern = ""

    if pos == "adj":
        if lemma_1_clean.endswith("a"):
            stem = lemma_1_clean[:-1]
            pattern = "a adj"
        if lemma_1_clean.endswith("ī"):
            stem = lemma_1_clean[:-1]
            pattern = "ī adj"
        if lemma_1_clean.endswith("ant"):
            stem = lemma_1_clean[:-3]
            pattern = "ant adj"
        if lemma_1_clean.endswith("u"):
            stem = lemma_1_clean[:-1]
            pattern = "u adj"
        if lemma_1_clean.endswith("i"):
            stem = lemma_1_clean[:-1]
            pattern = "i adj"
        if lemma_1_clean.endswith("ū"):
            stem = lemma_1_clean[:-1]
            pattern = "ū adj"
        if lemma_1_clean.endswith("aka"):
            stem = lemma_1_clean[:-3]
            pattern = "aka adj"

    elif pos == "masc":
        if lemma_1_clean.endswith("a"):
            stem = lemma_1_clean[:-1]
            pattern = "a masc"
        if lemma_1_clean.endswith("ī"):
            stem = lemma_1_clean[:-1]
            pattern = "ī masc"
        if lemma_1_clean.endswith("i"):
            stem = lemma_1_clean[:-1]
            pattern = "i masc"
        if lemma_1_clean.endswith("u"):
            stem = lemma_1_clean[:-1]
            pattern = "u masc"
        if lemma_1_clean.endswith("ar"):
            stem = lemma_1_clean[:-2]
            pattern = "ar masc"
        if lemma_1_clean.endswith("as"):
            stem = lemma_1_clean[:-1]
            pattern = "as masc"
        if lemma_1_clean.endswith("ū"):
            stem = lemma_1_clean[:-1]
            pattern = "ū masc"
        if lemma_1_clean.endswith("ant"):
            stem = lemma_1_clean[:-3]
            pattern = "ant masc"
        if lemma_1_clean.endswith("ā"):
            stem = lemma_1_clean[:-1]
            pattern = "a masc pl"
        if lemma_1_clean.endswith("as"):
            stem = lemma_1_clean[:-2]
            pattern = "as masc"

    elif pos == "fem":
        if lemma_1_clean.endswith("ā"):
            stem = lemma_1_clean[:-1]
            pattern = "ā fem"
        if lemma_1_clean.endswith("i"):
            stem = lemma_1_clean[:-1]
            pattern = "i fem"
        if lemma_1_clean.endswith("ī"):
            stem = lemma_1_clean[:-1]
            pattern = "ī fem"
        if lemma_1_clean.endswith("u"):
            stem = lemma_1_clean[:-1]
            pattern = "u fem"
        if lemma_1_clean.endswith("ar"):
            stem = lemma_1_clean[:-2]
            pattern = "ar fem"
        if lemma_1_clean.endswith("ū"):
            stem = lemma_1_clean[:-1]
            pattern = "ū fem"
        if lemma_1_clean.endswith("mātar"):
            stem = lemma_1_clean[:-5]
            pattern = "mātar fem"

    elif pos == "nt":
        if lemma_1_clean.endswith("a"):
            stem = lemma_1_clean[:-1]
            pattern = "a nt"
        if lemma_1_clean.endswith("u"):
            stem = lemma_1_clean[:-1]
            pattern = "u nt"
        if lemma_1_clean.endswith("i"):
            stem = lemma_1_clean[:-1]
            pattern = "i nt"

    elif pos == "card":
        if "x pl" in grammar:
            stem = lemma_1_clean[:-1]
            pattern = "a1 card"
        if "nt sg" in grammar:
            stem = lemma_1_clean[:-1]
            pattern = "a2 card"
        if lemma_1_clean.endswith("i"):
            stem = lemma_1_clean[:-1]
            pattern = "i card"
        if lemma_1_clean.endswith("koṭi"):
            stem = lemma_1_clean[:-1]
            pattern = "i2 card"
        if lemma_1_clean.endswith("ā"):
            stem = lemma_1_clean[:-1]
            pattern = "ā card"

    elif pos == "ordin":
        if lemma_1_clean.endswith("a"):
            stem = lemma_1_clean[:-1]
            pattern = "a ordin"

    elif pos == "pp":
        if lemma_1_clean.endswith("a"):
            stem = lemma_1_clean[:-1]
            pattern = "a pp"

    elif pos == "prp":
        if lemma_1_clean.endswith("anta"):
            stem = lemma_1_clean[:-4]
            pattern = "anta prp"
        if lemma_1_clean.endswith("enta"):
            stem = lemma_1_clean[:-4]
            pattern = "enta prp"
        if lemma_1_clean.endswith("onta"):
            stem = lemma_1_clean[:-4]
            pattern = "onta prp"
        if lemma_1_clean.endswith("māna"):
            stem = lemma_1_clean[:-4]
            pattern = "māna prp"
        elif lemma_1_clean.endswith("āna"):
            stem = lemma_1_clean[:-3]
            pattern = "āna prp"

    elif pos == "ptp":
        if lemma_1_clean.endswith("a"):
            stem = lemma_1_clean[:-1]
            pattern = "a ptp"

    elif pos == "pron":
        if lemma_1_clean.endswith("a"):
            stem = lemma_1_clean[:-1]
            pattern = "a pron"

    elif pos == "pr":
        if lemma_1_clean.endswith("ati"):
            stem = lemma_1_clean[:-3]
            pattern = "ati pr"
        if lemma_1_clean.endswith("eti"):
            stem = lemma_1_clean[:-3]
            pattern = "eti pr"
        if lemma_1_clean.endswith("oti"):
            stem = lemma_1_clean[:-3]
            pattern = "oti pr"
        if lemma_1_clean.endswith("āti"):
            stem = lemma_1_clean[:-3]
            pattern = "āti pr"

    elif pos == "aor":
        if lemma_1_clean.endswith("i"):
            stem = lemma_1_clean[:-1]
            pattern = "i aor"
        if lemma_1_clean.endswith("esi"):
            stem = lemma_1_clean[:-3]
            pattern = "esi aor"
        if lemma_1_clean.endswith("āsi"):
            stem = lemma_1_clean[:-3]
            pattern = "āsi aor"

    elif pos == "perf":
        if lemma_1_clean.endswith("a"):
            stem = lemma_1_clean[:-1]
            pattern = "a perf"

    elif pos == "imperf":
        if lemma_1_clean.endswith("ā"):
            stem = lemma_1_clean[:-1]
            pattern = "ā imperf"

    elif pos in INDECLINABLES:
        stem = "-"
        pattern = ""

    return stem, pattern


# !!! add all the plural forms !!!
