"""Functions for:
1. Summarizing meaning and literal meaning,
2. Summarizing construction,
3. Cleaning construction of all brackets and phonetic changes,
4. Creating an HTML styled symbol of a word data's degree of completion."""

from pathlib import Path
import re

from db.db_helpers import get_db_session
from db.models import DpdHeadword


def make_meaning_combo(i: DpdHeadword) -> str:
    """Compile meaning_1 and literal meaning, or return meaning_2."""
    if i.meaning_1:
        meaning: str = i.meaning_1
        if i.meaning_lit:
            meaning += f"; lit. {i.meaning_lit}"
        return meaning
    elif i.meaning_2:
        return i.meaning_2
    else:
        return ""


def make_meaning_combo_html(i: DpdHeadword) -> str:
    """Compile meaning_1 in bold tags and meaning_lit,
    or return meaning_2 and meaning_lit."""

    if i.meaning_1:
        meaning: str = f"<b>{i.meaning_1}</b>"
        if i.meaning_lit:
            meaning += f"; lit. {i.meaning_lit}"
        return meaning
    else:
        if "; lit." in i.meaning_2:
            return i.meaning_2
        elif i.meaning_lit:
            return f"{i.meaning_2}; lit. {i.meaning_lit}"
        else:
            return i.meaning_2


def make_grammar_line(i: DpdHeadword) -> str:
    """Compile grammar line"""

    grammar = i.grammar
    if i.neg:
        grammar += f", {i.neg}"
    if i.verb:
        grammar += f", {i.verb}"
    if i.trans:
        grammar += f", {i.trans}"
    if i.plus_case:
        grammar += f" ({i.plus_case})"
    return grammar


def summarize_construction(i: DpdHeadword) -> str:
    """Create a summary of a word's construction,
    excluding brackets and phonetic changes."""

    construction = i.construction.replace("<b>", "").replace("</b>", "")

    # if no meaning then show root, word family or nothing
    if not i.meaning_1 and i.origin not in ["pass1", "pass2"]:
        if i.root_key:
            return i.family_root.replace(" ", " + ")
        elif i.family_word:
            return i.family_word
        else:
            return ""

    elif i.meaning_1 or (not i.meaning_1 and i.origin in ["pass1", "pass2"]):
        if not i.construction:
            return ""

        # clean construction
        # remove line2
        construction = re.sub(r"\n.+$", "", construction)
        # remove phonetic changes
        construction = re.sub("> .[^ ]*? ", "", construction)
        # remove phonetic changes at end
        construction = re.sub(" > .[^ ]*?$", "", construction)
        # remove brackets
        construction = construction.replace("(", "").replace(")", "")
        # remove [insertions]
        construction = re.sub(r"^\[.*\] \+| \[.*\] \+| \+ \[.*\]$", "", construction)

        if not i.root_base:
            if construction:
                return construction
            else:
                return ""

        else:
            # cleanup the base and base_construction
            # remove types
            base_clean = re.sub(" \\(.+\\)$", "", i.root_base)
            # remove base root + sign
            base = re.sub("(.+ )(.+?$)", "\\2", base_clean)
            # remove base
            base_construction = re.sub("(.+)( > .+?$)", "\\1", base_clean)
            # remove phonetic changes
            base_construction = re.sub(" >.*", "", base_construction)

            if i.pos != "fut":
                # replace base with root + sign
                root_sign_plus = i.root_sign.replace(" ", " + ")
                root_plus_sign = f"{i.root_clean} + {root_sign_plus}"
                construction = re.sub(base, root_plus_sign, construction)
            else:
                # replace base with base construction
                construction = re.sub(base, base_construction, construction)
            return construction
    else:
        return ""


def clean_construction(construction):
    """Clean construction of all brackets and phonetic changes."""
    # strip line 2
    construction = re.sub(r"\n.+", "", construction)
    # remove > ... +
    construction = re.sub(r" >.+?( \+)", "\\1", construction)
    # remove [] ... +
    construction = re.sub(r" \+ \[.+?( \+)", "\\1", construction)
    # remove [] at beginning
    construction = re.sub(r"^\[.+?( \+ )", "", construction)
    # remove [] at end
    construction = re.sub(r" \+ \[.*\]$", "", construction)
    # remove ??
    construction = re.sub("\\?\\? ", "", construction)
    return construction


if __name__ == "__main__":
    session = get_db_session(Path("dpd.db"))
    results = (
        session.query(DpdHeadword)
        .filter(DpdHeadword.root_sign.contains(" "))
        .limit(50)
        .all()
    )
    for i in results:
        print(i.lemma_1, ": ", summarize_construction(i))
