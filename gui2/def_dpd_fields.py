import re

from tools.pos import INDECLINABLES


def clean_lemma_1(lemma_1: str) -> str:
    return re.sub(r" \d.*", "", lemma_1)


def clean_root(root_key: str) -> str:
    return re.sub(r" \d.*", "", root_key)


def clean_root_sign(root_sign: str) -> str:
    return re.sub(r"\*", "", root_sign)


def make_lemma_2(lemma_1: str, pos: str) -> str:
    lemma_clean = clean_lemma_1(lemma_1)
    if pos == "masc":
        if lemma_clean.endswith("a"):
            return f"{lemma_clean[:-1]}o"
        else:
            return lemma_clean
    elif pos == "nt":
        return f"{lemma_clean}ṃ"
    else:
        return lemma_1


def make_construction(
    lemma_clean: str,
    grammar: str,
    neg: str,
    root_key: str,
    root_base: str,
    root_family: str,
) -> str:
    """Make construction out of existing fields"""

    # root
    if root_key:
        root_family_x = root_family.replace(" ", " + ")
        neg_x = ""
        if neg:
            neg_x = "na + "
        if root_base:
            root_base_x = re.sub(r" \(.+\)$", "", root_base)  # remove (end brackets)
            root_base_x = re.sub("^.+> ", "", root_base_x)  # remove front
            root_family_x = re.sub("√.+", root_base_x, root_family_x)

        return f"{neg_x}{root_family_x} + "

    # compound
    elif re.findall(r"\bcomp\b", grammar):
        return lemma_clean
    else:
        return lemma_clean


def clean_construction_line1(construction) -> str:
    # remove line 2
    construction = re.sub(r"\n.+", "", construction)
    # remove phonetic changes >
    construction = re.sub(r">.[^+]+", "", construction)
    return construction


def find_stem_pattern(pos: str, grammar: str, lemma_1: str) -> tuple[str, str]:
    lemma_1_clean = clean_lemma_1(lemma_1)

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
