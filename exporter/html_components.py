import re

from rich import print
from mako.template import Template
from datetime import date
from sqlalchemy import or_

from db.models import PaliWord
from db.models import PaliRoot
from db.models import DerivedData
from db.models import FamilyRoot
from db.models import FamilyWord
from db.models import FamilyCompound
from db.models import FamilySet
from db.models import Sandhi

from helpers import get_paths
from helpers import CF_SET
from helpers import EXCLUDE_FROM_SETS
from helpers import EXCLUDE_FROM_FREQ

from tools.pos import CONJUGATIONS
from tools.pos import DECLENSIONS
from tools.pos import INDECLINEABLES
from tools.pali_sort_key import pali_sort_key

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
family_word_templ = Template(
    filename=str(PTH.family_word_templ_path))
family_compound_templ = Template(
    filename=str(PTH.family_compound_templ_path))
family_set_templ = Template(
    filename=str(PTH.family_set_templ_path))
frequency_templ = Template(
    filename=str(PTH.frequency_templ_path))
feedback_templ = Template(
    filename=str(PTH.feedback_templ_path))
root_definition_templ = Template(
    filename=str(PTH.root_definition_templ_path))
root_buttons_templ = Template(
    filename=str(PTH.root_button_templ_path))
root_info_templ = Template(
    filename=str(PTH.root_info_templ_path))
root_matrix_templ = Template(
    filename=str(PTH.root_matrix_templ_path))
root_families_templ = Template(
    filename=str(PTH.root_families_templ_path))
sandhi_templ = Template(
    filename=str(PTH.sandhi_templ_path)
)
epd_templ = Template(
    filename=str(PTH.epd_templ_path))
abbrev_templ = Template(
    filename=str(PTH.abbrev_templ_path))
help_templ = Template(
    filename=str(PTH.help_templ_path))


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
            complete = " <span class='gray'>✓</span>"
        else:
            complete = " <span class='gray'>~</span>"
    else:
        complete = " <span class='gray'>✗</span>"

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
            constr = re.sub("<br>.+$", "", i.construction)
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
            constr_oneline = re.sub("<br>.+", "", i.construction)
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
            target=f"root_family_{i.pali_1_}", name="root family")
    else:
        root_family_button = ""

    # word_family_button
    if i.family_word != "":
        word_family_button = button_html.format(
            target=f"word_family_{i.pali_1_}", name="word family")
    else:
        word_family_button = ""

    # compound_family_button
    if (i.meaning_1 != "" and
        (i.family_compound != "" or
            i.pali_clean in CF_SET)):

        if " " not in i.family_compound:
            compound_family_button = button_html.format(
                target=f"compound_family_{i.pali_1_}", name="compound family")

        else:
            compound_family_button = button_html.format(
                target=f"compound_family_{i.pali_1_}", name="compound familes")

    else:
        compound_family_button = ""

    # set_family_button
    set_list: list = _set_list_gen(i)
    if len(set_list) > 0:
        set_family_button = button_html.format(
            target=f"set_family_{i.pali_1_}", name="set")
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

    if fr is not None:

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


def render_family_word_templ(i: PaliWord, fw: FamilyWord) -> str:
    """render html of all words which belong to the same family"""

    if i.family_word != "":
        return str(
            family_word_templ.render(
                i=i,
                fw=fw,
                today=TODAY,
            )
        )
    else:
        return ""


def render_family_compound_templ(i: PaliWord, DB_SESSION) -> str:
    """render html table of all words containing the same compound"""

    if (i.meaning_1 != "" and
        (i.family_compound != "" or
            i.pali_clean in CF_SET)):

        fc = DB_SESSION.query(
            FamilyCompound
        ).filter(
            or_(
                FamilyCompound.compound_family.in_(i.family_compound_list),
                FamilyCompound.compound_family == i.pali_clean
            )
        ).all()

        return str(
            family_compound_templ.render(
                i=i,
                fc=fc,
                today=TODAY,
            )
        )
    else:
        return ""


def render_family_sets_templ(i: PaliWord, DB_SESSION) -> str:
    """render html table of all words belonging to the same set"""

    if (i.meaning_1 != "" and
            i.family_set != ""):
        set_list: list = _set_list_gen(i)

        if len(set_list) > 0:

            fs = DB_SESSION.query(
                FamilySet
            ).filter(
                FamilySet.set.in_(set_list)
            ).all()

            return str(
                family_set_templ.render(
                    i=i,
                    fs=fs,
                    today=TODAY,
                )
            )
        else:
            return ""
    else:
        return ""


def _set_list_gen(i: PaliWord) -> list:
    """exlcude unnecessary sets"""
    return [set for set in i.family_set.split("; ")
            if set and set not in EXCLUDE_FROM_SETS]


def render_frequency_templ(i: PaliWord, dd: DerivedData) -> str:
    """render html tempalte of freqency table"""

    if i.pos not in EXCLUDE_FROM_FREQ:

        return str(
            frequency_templ.render(
                i=i,
                dd=dd,
                today=TODAY,
            )
        )
    else:
        return ""


def render_feedback_templ(i: PaliWord) -> str:
    """render html of feedback template"""

    return str(
        feedback_templ.render(
            i=i,
            today=TODAY,
        )
    )


def render_root_definition_templ(r: PaliRoot, info: PaliRoot):
    """render html of main root info"""

    count = info.count

    return str(
        root_definition_templ.render(
            r=r,
            count=count,
            today=TODAY,
        )
    )


def render_root_buttons_templ(r: PaliRoot, DB_SESSION):
    """render html of root buttons"""

    frs = DB_SESSION.query(
        FamilyRoot
        ).filter(
            FamilyRoot.root_id == r.root,
            FamilyRoot.root_family != "info",
            FamilyRoot.root_family != "matrix",
        )

    frs = sorted(frs, key=lambda x: pali_sort_key(x.root_family))

    return str(
        root_buttons_templ.render(
            r=r,
            frs=frs,
        )
    )


def render_root_info_templ(r: PaliRoot, info: PaliRoot):
    """render html of root grammatical info"""

    return str(
        root_info_templ.render(
            r=r,
            info=info,
            today=TODAY
        )
    )


def render_root_matrix_templ(r: PaliRoot, DB_SESSION):
    """render html of root matrix"""

    fr = DB_SESSION.query(
        FamilyRoot
    ).filter(
        FamilyRoot.root_id == r.root,
        FamilyRoot.root_family == "matrix",
    ).first()

    return str(
        root_matrix_templ.render(
            r=r,
            fr=fr,
            today=TODAY
        )
    )


def render_root_families_templ(r: PaliRoot, DB_SESSION):
    """render html of root families"""

    frs = DB_SESSION.query(
        FamilyRoot
        ).filter(
            FamilyRoot.root_id == r.root,
            FamilyRoot.root_family != "info",
            FamilyRoot.root_family != "matrix",
        ).all()

    frs = sorted(frs, key=lambda x: pali_sort_key(x.root_family))

    return str(
        root_families_templ.render(
            r=r,
            frs=frs,
            today=TODAY
        )
    )


def render_sandhi_templ(splits: list) -> str:
    return str(
        sandhi_templ.render(
            splits=splits,
            today=TODAY
        )
    )


def render_abbrev_templ(i) -> str:
    """render html of abbreviations"""
    return str(
        abbrev_templ.render(
            i=i,
        )
    )


def render_help_templ(i) -> str:
    """render html of help"""
    return str(
        help_templ.render(
            i=i,
        )
    )
