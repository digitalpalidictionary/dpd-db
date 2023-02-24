import re

from mako.template import Template
from datetime import date

from db.models import PaliWord, DerivedData, FamilyRoot
from helpers import get_paths
from helpers import CONJUGATIONS
from helpers import DECLENSIONS
from helpers import INDECLINEABLES
from helpers import CF_SET
from helpers import EXCLUDE_FROM_CATEGORIES
from helpers import EXCLUDE_FROM_FREQ

TODAY = date.today()
PTH = get_paths()

header_tmpl = Template(
    filename=str(PTH.header_templ_path))

dpd_definition_templ = Template(
    filename=str(PTH.dpd_definition_templ_path))

button_box_templ = Template(
    filename=str(PTH.button_box_templ_path))

grammar_templ = Template(
    filename=str(PTH.grammar_templ_path))

example_templ = Template(
    filename=str(PTH.example_templ_path))

inflection_templ = Template(
    filename=str(PTH.inflection_templ_path))

family_root_templ = Template(
    filename=str(PTH.family_root_templ_path))


def render_header_tmpl(css: str, js: str) -> str:
    """render the html header with css and js"""
    return str(header_tmpl.render(css=css, js=js))


def render_dpd_defintion_templ(i: PaliWord) -> str:
    """render the definition of a word's most relevant information:
    1. pos
    2. case
    3 meaning
    4. summary
    5. degree of completition"""

    # pos
    pos: str = f"{i.pos}."

    # plus_case
    plus_case: str = ""
    if i.plus_case != "":
        plus_case: str = f" ({i.plus_case}) "

    meaning = f" {_make_meaning(i)}"

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
            complete=complete
        )
    )


def _make_meaning(i: PaliWord) -> str:
    """compile meaning_1 and literal meaning
    or return meaning_2"""

    if i.meaning_1 != "":
        meaning: str = f"<b>{i.meaning_1}</b>"
        if i.meaning_lit != "":
            meaning += f"; lit. {i.meaning_lit}"
        return meaning
    else:
        return f"<b>{i.meaning_2}</b>"


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
                constr_trunc = re.sub(r"na > a|a > an|a > ana", "", constr_trunc)
            else:
                constr_na = ""

            constr_reconstr = f"{constr_na}{family_plus} + {i.root_sign}{constr_trunc}"
            return fr" [{constr_reconstr}]"

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
            return fr" [{constr_reconstr}]"


def render_button_box_templ(i: PaliWord) -> str:
    """render buttons for each section of the dictionary"""

    button_html = (
        '<a class="button" '
        'href="javascript:void(0);" '
        'onclick="button_click(this)" '
        'data-target="{target}">{name}</a>'
    )

    # grammar_button
    if i.meaning_1 != "":
        grammar_button = button_html.format(
            target=f"grammar_{i.pali_1_}", name="grammar")
    else:
        grammar_button = ""

    # example_button
    if i.meaning_1 != "" and i.example_1 != "" and i.example_2 == "":
        example_button = button_html.format(
            target=f"example_{i.pali_1_}", name="example")
    else:
        example_button = ""

    # examples_button
    if i.meaning_1 != "" and i.example_1 != "" and i.example_2 != "":
        examples_button = button_html.format(
            target=f"examples_{i.pali_1_}", name="examples")
    else:
        examples_button = ""

    # conjugation_button
    if i.pos in CONJUGATIONS:
        conjugation_button = button_html.format(
            target=f"conjugation_{i.pali_1_}", name="conjugation")
    else:
        conjugation_button = ""

    # declension_button
    if i.pos in DECLENSIONS:
        declension_button = button_html.format(
            target=f"declension_{i.pali_1_}", name="declension")
    else:
        declension_button = ""

    # root_family_button
    if i.family_root != "":
        root_family_button = button_html.format(
            target=f"root_family_{i.pali_1_}", name="root_family")
    else:
        root_family_button = ""

    # word_family_button
    if i.family_word != "":
        word_family_button = button_html.format(
            target=f"word_family_{i.pali_1_}", name="word_family")
    else:
        word_family_button = ""

    # compound_family_button
    # !!!!!!!!!!!!!!!!!!!!!! add if i.meaning_1 != "" and
    if (" " not in i.family_compound and
        (i.family_compound != "" or
            i.pali_clean in CF_SET)):
        compound_family_button = button_html.format(
            target=f"compound_family_{i.pali_1_}", name="compound_family")
    else:
        compound_family_button = ""

    # compound_families_button
    # !!!!!!!!!!!!!!!!!!!!!! add if i.meaning_1 != "" and
    if (" " in i.family_compound and
        (i.family_compound != "" or
            i.pali_clean in CF_SET)):
        compound_family_button = button_html.format(
            target=f"compound_family_{i.pali_1_}", name="compound_family")
    else:
        compound_family_button = ""

    # set_family_button
    if (i.category != "" and i.category not in EXCLUDE_FROM_CATEGORIES):
        set_family_button = button_html.format(
            target=f"set_family_{i.pali_1_}", name="set_family")
    else:
        set_family_button = ""

    # frequency_button
    if i.pos not in EXCLUDE_FROM_FREQ:
        frequency_button = button_html.format(
            target=f"frequency_{i.pali_1_}", name="frequency")
    else:
        frequency_button = ""

    # feedback_button
    feedback_button = button_html.format(
        target=f"feedback_{i.pali_1_}", name="feedback")

    return str(
        button_box_templ.render(
            grammar_button=grammar_button,
            example_button=example_button,
            examples_button=examples_button,
            conjugation_button=conjugation_button,
            declension_button=declension_button,
            root_family_button=root_family_button,
            word_family_button=word_family_button,
            compound_family_button=compound_family_button,
            compound_families_button=compound_family_button,
            set_family_button=set_family_button,
            frequency_button=frequency_button,
            feedback_button=feedback_button
        )
    )


def render_grammar_templ(i: PaliWord) -> str:
    """html table of grammatical information"""

    if i.meaning_1 != "":

        grammar = i.grammar
        if i.neg != "":
            grammar += f", {i.neg}"
        if i.verb != "":
            grammar += f", {i.verb}"
        if i.trans != "":
            grammar += f", {i.trans}"
        if i.plus_case != "":
            grammar += f" ({i.plus_case})"

        meaning = f"{_make_meaning(i)}"

        return str(
            grammar_templ.render(
                i=i,
                grammar=grammar,
                meaning=meaning,
                today=TODAY,
            )
        )

    else:
        return ""


def render_example_templ(i: PaliWord) -> str:
    """render sutta examples html"""

    if i.meaning_1 != "" and i.example_1 != "":
        return str(
            example_templ.render(
                i=i,
                today=TODAY
            )
        )
    else:
        return ""


def render_inflection_templ(i: PaliWord, dd: DerivedData) -> str:
    """inflection or conjugation table"""
    if i.pos not in INDECLINEABLES:

        return str(
            inflection_templ.render(
                i=i,
                table=dd.html_table,
                today=TODAY,
                declensions=DECLENSIONS,
                conjugations=CONJUGATIONS,
            )
        )
    else:
        return ""


def render_family_root_templ(i: PaliWord, fr: FamilyRoot) -> str:
    """render html table of all words with the same prefix and root"""

    if i.family_root != "":
        return str(
            family_root_templ.render(
                i=i,
                fr=fr,
                today=TODAY,
            )
        )
    else:
        return ""
