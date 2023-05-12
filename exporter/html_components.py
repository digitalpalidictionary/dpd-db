import re

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

from helpers import CF_SET
from helpers import EXCLUDE_FROM_SETS
from helpers import EXCLUDE_FROM_FREQ

from tools.paths import ProjectPaths as PTH
from tools.pos import CONJUGATIONS
from tools.pos import DECLENSIONS
from tools.pos import INDECLINEABLES
from tools.pali_sort_key import pali_sort_key
from tools.meaning_construction import make_meaning_html
from tools.meaning_construction import summarize_constr
from tools.meaning_construction import degree_of_completion

TODAY = date.today()

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
    pos: str = i.pos

    # plus_case
    plus_case: str = ""
    if i.plus_case != "":
        plus_case: str = i.plus_case

    meaning = make_meaning_html(i)
    summary = summarize_constr(i)
    complete = degree_of_completion(i)

    return str(
        dpd_definition_templ.render(
            pos=pos,
            plus_case=plus_case,
            meaning=meaning,
            summary=summary,
            complete=complete))


def render_button_box_templ(i: PaliWord) -> str:
    """render buttons for each section of the dictionary"""

    button_html = (
        '<a class="button" '
        'href="javascript:void(0);" '
        'onclick="button_click(this)" '
        'data-target="{target}">{name}</a>')

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
    if (i.meaning_1 != "" and
            i.family_set != ""):

        if len(i.family_set_list) > 0:
            set_family_button = button_html.format(
                target=f"set_family_{i.pali_1_}", name="set")
        else:
            set_family_button = ""
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
            feedback_button=feedback_button))


def render_grammar_templ(i: PaliWord) -> str:
    """html table of grammatical information"""

    if i.meaning_1 != "":
        i.construction = i.construction.replace("\n", "<br>")

        grammar = i.grammar
        if i.neg != "":
            grammar += f", {i.neg}"
        if i.verb != "":
            grammar += f", {i.verb}"
        if i.trans != "":
            grammar += f", {i.trans}"
        if i.plus_case != "":
            grammar += f" ({i.plus_case})"

        meaning = f"<b>{make_meaning_html(i)}</b>"

        return str(
            grammar_templ.render(
                i=i,
                grammar=grammar,
                meaning=meaning,
                today=TODAY))

    else:
        return ""


def render_example_templ(i: PaliWord) -> str:
    """render sutta examples html"""

    if i.meaning_1 != "" and i.example_1 != "":
        return str(
            example_templ.render(
                i=i,
                today=TODAY))
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
                conjugations=CONJUGATIONS))
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
                    today=TODAY))
    else:
        return ""


def render_family_word_templ(i: PaliWord, fw: FamilyWord) -> str:
    """render html of all words which belong to the same family"""

    if i.family_word != "":
        return str(
            family_word_templ.render(
                i=i,
                fw=fw,
                today=TODAY))
    else:
        return ""


def render_family_compound_templ(i: PaliWord, DB_SESSION) -> str:
    """render html table of all words containing the same compound"""

    if (i.meaning_1 != "" and
        (i.family_compound != "" or
            i.pali_clean in CF_SET)):

        if i.family_compound != "":
            fc = DB_SESSION.query(
                FamilyCompound
            ).filter(
                FamilyCompound.compound_family.in_(i.family_compound_list),
                    # FamilyCompound.compound_family == i.pali_clean
            ).all()

            # sort by order of the  family compound list
            word_order = i.family_compound_list
            fc = sorted(fc, key=lambda x: word_order.index(x.compound_family))

        else:
            fc = DB_SESSION.query(
                FamilyCompound
            ).filter(
                FamilyCompound.compound_family == i.pali_clean
            ).all()

        return str(
            family_compound_templ.render(
                i=i,
                fc=fc,
                today=TODAY))
    else:
        return ""


def render_family_sets_templ(i: PaliWord, DB_SESSION) -> str:
    """render html table of all words belonging to the same set"""

    if (i.meaning_1 != "" and
            i.family_set != ""):

        if len(i.family_set_list) > 0:

            fs = DB_SESSION.query(
                FamilySet
            ).filter(
                FamilySet.set.in_(i.family_set_list)
            ).all()

            # sort by order of the  family set list
            word_order = i.family_set_list
            fs = sorted(fs, key=lambda x: word_order.index(x.set))

            return str(
                family_set_templ.render(
                    i=i,
                    fs=fs,
                    today=TODAY))
        else:
            return ""
    else:
        return ""


def render_frequency_templ(i: PaliWord, dd: DerivedData) -> str:
    """render html tempalte of freqency table"""

    if i.pos not in EXCLUDE_FROM_FREQ:

        return str(
            frequency_templ.render(
                i=i,
                dd=dd,
                today=TODAY))
    else:
        return ""


def render_feedback_templ(i: PaliWord) -> str:
    """render html of feedback template"""

    return str(
        feedback_templ.render(
            i=i,
            today=TODAY))


def render_root_definition_templ(r: PaliRoot, roots_count_dict):
    """render html of main root info"""

    count = roots_count_dict[r.root]

    return str(
        root_definition_templ.render(
            r=r,
            count=count,
            today=TODAY))


def render_root_buttons_templ(r: PaliRoot, DB_SESSION):
    """render html of root buttons"""

    frs = DB_SESSION.query(
        FamilyRoot
        ).filter(
            FamilyRoot.root_id == r.root)

    frs = sorted(frs, key=lambda x: pali_sort_key(x.root_family))

    return str(
        root_buttons_templ.render(
            r=r,
            frs=frs))


def render_root_info_templ(r: PaliRoot):
    """render html of root grammatical info"""

    return str(
        root_info_templ.render(
            r=r,
            today=TODAY))


def render_root_matrix_templ(r: PaliRoot, roots_count_dict):
    """render html of root matrix"""
    count = roots_count_dict[r.root]

    return str(
        root_matrix_templ.render(
            r=r,
            count=count,
            today=TODAY))


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
            today=TODAY))


def render_sandhi_templ(i, splits: list) -> str:
    return str(
        sandhi_templ.render(
            i=i,
            splits=splits,
            today=TODAY))


def render_abbrev_templ(i) -> str:
    """render html of abbreviations"""
    return str(
        abbrev_templ.render(
            i=i))


def render_help_templ(i) -> str:
    """render html of help"""
    return str(
        help_templ.render(
            i=i))
