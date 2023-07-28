"""Functions for:
1. Summarizating meaning and literal meaning,
2. Summarizating construction,
3. Cleaning construction of all brackets and phonetic changes,
4. Creating an HTML styled symbol of a word data's degree of complettion."""

import re
from db.models import PaliWord


def make_meaning(i: PaliWord) -> str:
    """Compile meaning_1 and literal meaning, or return meaning_2."""
    if i.meaning_1:
        meaning: str = i.meaning_1
        if i.meaning_lit:
            meaning += f"; lit. {i.meaning_lit}"
        return meaning
    else:
        return i.meaning_2


def make_meaning_html(i: PaliWord) -> str:
    """Compile html of meaning_1 and literal meaning, or return meaning_2.
    Meaning_1 in <b>bold</b>"""

    if i.meaning_1:
        meaning: str = f"<b>{i.meaning_1}</b>"
        if i.meaning_lit:
            meaning += f"; lit. {i.meaning_lit}"
        return meaning
    else:
        # add bold to meaning_2, keep lit. plain
        if "; lit." in i.meaning_2:
            return re.sub("(.+)(; lit.+)", "<b>\\1</b>\\2", i.meaning_2)
        else:
            return f"<b>{i.meaning_2}</b>"


def summarize_constr(i: PaliWord) -> str:
    """Create a summary of a word's construction,
    exlucing brackets and phonetic changes."""
    if "<b>" in i.construction:
        i.construction = i.construction.replace("<b>", "").replace("</b>", "")

    # if no meaning then show root, word family or nothing
    if i.meaning_1 == "":
        if i.root_key:
            return i.family_root.replace(" ", " + ")
        elif i.family_word:
            return i.family_word
        else:
            return ""

    else:
        if i.construction == "":
            return ""

        elif i.root_base == "":
            # remove line2
            constr = re.sub(r"\n.+$", "", i.construction)
            # remove [insertions]
            constr = re.sub(r"^\[.*\] \+| \[.*\] \+", "", constr)
            # remove phonetic changes
            constr = re.sub("> .[^ ]*? ", "", constr)
            # remove phonetic changes at end
            constr = re.sub(" > .[^ ]*?$", "", constr)

            if constr != "":
                return f"{constr}"
            else:
                return ""

        elif i.root_base != "" and i.pos != "fut":
            base_clean = re.sub(" \\(.+\\)$", "", i.root_base)
            base_clean = re.sub("(.+ )(.+?$)", "\\2", base_clean)
            family_plus = re.sub(" ", " + ", i.family_root)
            constr_oneline = re.sub(r"\n.+", "", i.construction)
            constr_trunc = re.sub(" > .[^ ]+", "", constr_oneline)
            constr_trunc = re.sub(f".*{base_clean}", "", constr_trunc)

            # look for na in front
            if re.match("^na ", i.construction):
                constr_prefix = re.sub("^(na )(.+)$", "\\1+ ", constr_oneline)
                constr_trunc = re.sub(
                    r"na > a|a > an|a > ana", "", constr_trunc)
            # look for other prefixes in front
            elif re.match("^sa ", i.construction):
                constr_prefix = "sa + "
            elif re.match("^a ", i.construction):
                constr_prefix = "a + "
            elif re.match("^ku ", i.construction):
                constr_prefix = "ku + "
            else:
                constr_prefix = ""

            constr_reconstr = f"{constr_prefix}{family_plus} + "
            constr_reconstr += f"{i.root_sign}{constr_trunc}"
            return constr_reconstr

        elif i.root_base != "" and i.pos == "fut":
            # remove > base and end brackets
            base = re.sub(" > .+ \\(.+\\)$", "", i.root_base)
            # remove root
            base = re.sub("√.[^ ]* \\+ ", "", base)
            # family prefix
            family_prefix = re.sub(" ", " + ", i.family_root)
            # remove phonetic changes
            constr_trunc = re.sub(" > .[^ ]+", "", i.construction)
            # only keep ending
            constr_trunc = re.sub(r"(.+)( \+ .*$)", "\\2", constr_trunc)

            if re.match("^na ", i.construction):
                constr_prefix = re.sub(
                    "^(na )(.+)$", "\\1+ ", i.construction)
                constr_trunc = re.sub(
                    r"na > a|a > an|a > ana", "", constr_trunc)
            else:
                constr_prefix = ""

            constr_reconstr = f"{constr_prefix}{family_prefix} + "
            constr_reconstr += f"{base}{constr_trunc}"
            return constr_reconstr


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
    # remove ??
    construction = re.sub("\\?\\? ", "", construction)
    return construction


def degree_of_completion(i):
    """Return html styled symbol of a word data degree of completion."""
    if i.meaning_1:
        if i.source_1:
            return """<span class="gray">✓</span>"""
        else:
            return """<span class="gray">~</span>"""
    else:
        return """<span class="gray">✗</span>"""
