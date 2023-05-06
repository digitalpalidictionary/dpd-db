import re
from db.models import PaliWord


def make_meaning(i: PaliWord) -> str:
    """compile meaning_1 and literal meaning
    or return meaning_2"""

    if i.meaning_1 != "":
        meaning: str = f"<b>{i.meaning_1}</b>"
        if i.meaning_lit != "":
            meaning += f"; lit. {i.meaning_lit}"
        return meaning
    else:
        return f"<b>{i.meaning_2}</b>"


def summarize_constr(i: PaliWord) -> str:
    """create a summary of the word's construction"""

    if i.construction == "" or i.meaning_1 == "":
        return ""

    else:
        if i.root_base == "":
            # remove line2
            constr = re.sub(r"<br>.+$", "", i.construction)
            # remove [insertions]
            constr = re.sub(r" \[.+\] \+", "", constr)
            # remove phonetic changes
            constr = re.sub("> .[^ ]*? ", "", constr)
            # remove phonetic changes at end
            constr = re.sub(" > .[^ ]*?$", "", constr)

            if constr != "":
                return f"{constr}"
            else:
                return ""

        if i.root_base != "" and i.pos != "fut":
            base_clean = re.sub(" \\(.+\\)$", "", i.root_base)
            base_clean = re.sub("(.+ )(.+?$)", "\\2", base_clean)
            family_plus = re.sub(" ", " + ", i.family_root)
            constr_oneline = re.sub(r"<br>.+", "", i.construction)
            constr_trunc = re.sub(" > .[^ ]+", "", constr_oneline)
            constr_trunc = re.sub(f".*{base_clean}", "", constr_trunc)

            if re.match("^na ", i.construction):
                constr_na = re.sub("^(na )(.+)$", "\\1+ ", i.construction)
                constr_trunc = re.sub(r"na > a|a > an|a > ana", "", constr_trunc)
            else:
                constr_na = ""

            constr_reconstr = f"{constr_na}{family_plus} + {i.root_sign}{constr_trunc}"
            return fr"{constr_reconstr}"

        if i.root_base != "" and i.pos == "fut":
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
                constr_na = re.sub(
                    "^(na )(.+)$", "\\1+ ", i.construction)
                constr_trunc = re.sub(
                    r"na > a|a > an|a > ana", "", constr_trunc)
            else:
                constr_na = ""

            constr_reconstr = f"{constr_na}{family_prefix} + {base}{constr_trunc}"
            return fr"{constr_reconstr}"
