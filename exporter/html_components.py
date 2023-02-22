import re
from mako.template import Template

from db.models import PaliWord
from helpers import get_paths

PTH = get_paths()


def render_header_tmpl(css: str, js: str) -> str:
    """render the html header with css and js"""
    header_tmpl = Template(filename=str(PTH.header_tmpl_path))
    return str(header_tmpl.render(css=css, js=js))


def render_dpd_defintion_templ(i: PaliWord) -> str:
    """render the definition of a word's most relevant  information:
    1. pos
    2. case
    3 meaning
    4. summary
    5. degree of completition"""

    dpd_definition_templ = Template(filename=str(PTH.dpd_definition_path))

    # pos
    pos: str = f"{i.pos}."

    # plus_case
    plus_case: str = ""
    if i.plus_case != "":
        plus_case: str = f" ({i.plus_case}) "

    # meaning
    if i.meaning_1 != "":
        meaning: str = f" <b>{i.meaning_1}</b>"

        if i.meaning_lit != "":
            meaning += f"; lit. {i.meaning_lit}"

    else:
        meaning = f" <b>{i.meaning_2}</b>"

    summary = _summarize_constr(i)

    # complete
    if i.meaning_1 != "":
        if i.source_1 != "":
            complete = " <span class='g1'>✓</span>"
        else:
            complete = " <span class='g2'>~</span>"
    else:
        complete = " <span class='g3'>✗</span>"

    return str(
        dpd_definition_templ.render(
            pos=pos,
            plus_case=plus_case,
            meaning=meaning,
            summary=summary,
            complete=complete))


def _summarize_constr(i: PaliWord) -> str:
    """create a summary of the word's construction"""

    if i.construction == "" or i.meaning_1 == "":
        return ""

    else:
        if i.root_base == "":
            # remove line2
            constr = re.sub("<br/>.+$", "", i.construction)
            # remove [insertions]
            constr = re.sub(r" \[.+\] \+", "", constr)
            # remove phonetic changes
            constr = re.sub("> .[^ ]*? ", "", constr)
            # remove phonetic changes at end
            constr = re.sub(" > .[^ ]*?$", "", constr)

            if constr != "":
                return fr" [{constr}]"
            else:
                return ""

        if i.root_base != "" and i.pos != "fut":
            base_clean = re.sub(" \\(.+\\)$", "", i.root_base)
            base_clean = re.sub("(.+ )(.+?$)", "\\2", base_clean)
            family_plus = re.sub(" ", " + ", i.family_root)
            constr_oneline = re.sub("<br/>.+", "", i.construction)
            constr_trunc = re.sub(" > .[^ ]+", "", constr_oneline)
            constr_trunc = re.sub(f".*{base_clean}", "", constr_trunc)

            if re.match("^na ", i.construction):
                constr_na = re.sub("^(na )(.+)$", "\\1+ ", i.construction)
                constr_trunc = re.sub(r"na > aa > ana > ana", "", constr_trunc)
            else:
                constr_na = ""

            constr_reconstr = f"{constr_na}{family_plus} + {i.root_sign}{constr_trunc}"
            return fr" [{constr_reconstr}]"

        if i.root_base != "" and i.pos == "fut":
            # remove > base and end brackets
            base = re.sub(" > .+ \\(.+\\)$", "", i.root_base)
            base = re.sub("√.[^ ]* \\+ ", "", base)
            family_prefix = re.sub(" ", " + ", i.family_root)
            # remove phonetic changes
            constr_trunc = re.sub(" > .[^ ]+", "", i.construction)
            constr_trunc = re.sub(r"(.+)( \+ .*$)", "\\2", constr_trunc)

            if re.match("^na ", i.construction):
                constr_na = re.sub(
                    "^(na )(.+)$", "\\1+ ", i.construction)
                constr_trunc = re.sub(
                    r"na > aa > ana > ana", "", constr_trunc)
            else:
                constr_na = ""

            constr_reconstr = f"{constr_na}{family_prefix} + {base}{constr_trunc}"
            return fr" [{constr_reconstr}]"
