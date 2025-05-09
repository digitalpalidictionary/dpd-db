import re

from db.models import DpdHeadword
from tools.pali_alphabet import pali_alphabet
from tools.pos import INDECLINABLES
from tools.sandhi_contraction import SandhiContractionDict


def clean_lemma_1(lemma_1: str) -> str:
    return re.sub(r" \d.*", "", lemma_1).strip()


def increment_lemma_1(lemma_1: str) -> str:
    """Increments the number at the end of lemma_1 (e.g., word -> word 1, word 1 -> word 2)."""
    # Check if the string ends with a digit
    if lemma_1 and lemma_1[-1].isdigit():
        # Find the part before the last digit
        base = lemma_1[:-1]
        # Get the last digit, increment it
        last_digit_val = int(lemma_1[-1]) + 1
        # Combine them back (handles cases like '9' becoming '10')
        return f"{base}{last_digit_val}"
    else:
        # If no digit at the end, add ' 2'
        return f"{lemma_1} 2"


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
        return lemma_clean


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
        if lemma_1_clean.endswith("rāja"):
            stem = lemma_1_clean[:-4]
            pattern = "rāja masc"

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


def make_compound_construction_from_headword(headword: DpdHeadword) -> str:
    """Make compound_construction based on other fields."""
    lemma_clean = clean_lemma_1(headword.lemma_1)
    construction_line1 = clean_construction_line1(headword.construction)

    # roots starting with su dur na
    if headword.root_key:
        if headword.construction.startswith("su "):
            return f"su + {lemma_clean[2:]}"
        elif headword.construction.startswith("dur "):
            return f"dur + {lemma_clean[3:]}"
        elif headword.construction.startswith("na "):
            if lemma_clean.startswith("an"):
                return f"na + {lemma_clean[2:]}"
            elif lemma_clean.startswith("a"):
                return f"na + {lemma_clean[1:]}"
            elif lemma_clean.startswith("na"):
                return f"na + {lemma_clean[2:]}"

    # compounds
    elif re.findall(r"\bcomp\b", headword.grammar):
        return construction_line1

    # dvanda '+' > 'ca'
    elif headword.compound_type == "dvanda":
        return construction_line1.replace("+", " <b>ca</b>") + " <b>ca</b>"

    # neg kammadhārayas
    elif headword.compound_type == "kammadhāraya" and "neg" in headword.neg:
        if lemma_clean.startswith("na"):
            # check if there's a double consonant
            if len(lemma_clean) > 2 and lemma_clean[2] == lemma_clean[3]:
                return f"na + {lemma_clean[3:]}"
            else:
                return f"na + {lemma_clean[2:]}"
        elif lemma_clean.startswith("an"):
            return f"na + {lemma_clean[2:]}"
        elif lemma_clean.startswith("a"):
            # check if there's a double consonant
            if len(lemma_clean) > 1 and lemma_clean[1] == lemma_clean[2]:
                return f"na + {lemma_clean[2:]}"
            else:
                return f"na + {lemma_clean[1:]}"
        elif lemma_clean.startswith("nā"):
            return f"na + a{lemma_clean[2:]}"

    # Default case if none of the above match
    return lemma_clean


# TODO add all the plural forms


def make_dpd_headword_from_dict(field_data: dict[str, str]) -> DpdHeadword:
    """Creates a DpdHeadword object from a dictionary of field data."""

    new_word = DpdHeadword()
    for field_name, value in field_data.items():
        if hasattr(new_word, field_name):
            processed_value = (
                value.strip() if isinstance(value, str) else value
            )  # remove spaces
            processed_value = (
                processed_value.replace("  ", " ") if isinstance(value, str) else value
            )  # remove double spaces
            setattr(new_word, field_name, processed_value)
    return new_word


def clean_sandhi(
    text: str,
    sandhi_dict: SandhiContractionDict,
    hyphenation_dict: dict[str, str],
) -> str:
    pali_alphabet_string = "".join(pali_alphabet)
    splits = re.split(f"([^{pali_alphabet_string}])", text)

    for i in range(len(splits)):
        word = splits[i]
        if word in sandhi_dict:
            splits[i] = "//".join(sandhi_dict[word])

        if word in hyphenation_dict:
            splits[i] = hyphenation_dict[word]

    return "".join(splits)


def clean_text(text: str) -> str:
    # replace ṁ with ṃ
    text = text.replace("ṁ", "ṃ")
    # fix bold 'ti
    text = text.replace("</b>ti", "</b>'ti")
    # fix bold 'ti
    text = text.replace("</b>nti", "n</b>'ti")
    # fix 'n</b>'ti
    text = text.replace("'n</b>'ti", "n</b>'ti")
    # fix bold comma
    text = text.replace(",</b>", "</b>,")
    # fix bold stop
    text = text.replace(".</b>", "</b>.")
    # fix bold quote
    text = text.replace("'</b>'", "</b>'")
    # fix 'tipi
    text = text.replace("'tipi", "'ti'pi")
    # remove [...]
    text = re.sub(r"\[[^]]*\]", "", text)
    # remove double spaces
    text = re.sub(" +", " ", text)
    # remove digits in front
    text = re.sub(r"^\d*\. ", "", text)
    # remove space comma
    text = text.replace(" ,", ",")
    # remove space fullstop
    text = text.replace(" .", ".")
    # remove spaces front n back
    text = text.strip()

    return text


def clean_commentary(
    text: str,
    sandhi_dict: SandhiContractionDict,
    hyphenation_dict: dict[str, str],
) -> str:
    text = clean_sandhi(text, sandhi_dict, hyphenation_dict)
    text = clean_text(text)
    return text


def clean_example(
    text: str,
    sandhi_dict: SandhiContractionDict,
    hyphenation_dict: dict[str, str],
) -> str:
    text = clean_sandhi(text, sandhi_dict, hyphenation_dict)
    text = clean_text(text)
    return text
