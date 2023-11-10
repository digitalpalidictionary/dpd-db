"""Compile HTML data for PaliWord."""

from datetime import datetime
from tools.time_log import time_log
import psutil
from css_html_js_minify import css_minify, js_minify
from mako.template import Template
from minify_html import minify
from rich import print
from sqlalchemy import and_
from typing import List, Set, TypedDict, Tuple
from multiprocessing.managers import ListProxy
from multiprocessing import Process, Manager

from sqlalchemy.orm import object_session
from sqlalchemy.orm.session import Session

from helpers import EXCLUDE_FROM_FREQ
from helpers import TODAY

from db.models import PaliRoot, PaliWord
from db.models import DerivedData
from db.models import FamilyRoot
from db.models import FamilyWord
from db.models import FamilyCompound
from db.models import FamilySet

from tools.meaning_construction import make_meaning_html
from tools.meaning_construction import summarize_constr
from tools.meaning_construction import degree_of_completion
from tools.niggahitas import add_niggahitas
from tools.paths import ProjectPaths
from tools.pos import CONJUGATIONS
from tools.pos import DECLENSIONS
from tools.pos import INDECLINABLES
from tools.tic_toc import bip
from tools.configger import config_test
from tools.sandhi_contraction import SandhiContractions
from tools.utils import RenderResult, RenderedSizes, default_rendered_sizes, list_into_batches, sum_rendered_sizes

class PaliWordTemplates:
    def __init__(self, pth: ProjectPaths):
        self.header_templ = Template(filename=str(pth.header_templ_path))
        self.dpd_definition_templ = Template(filename=str(pth.dpd_definition_templ_path))
        self.button_box_templ = Template(filename=str(pth.button_box_templ_path))
        self.grammar_templ = Template(filename=str(pth.grammar_templ_path))
        self.example_templ = Template(filename=str(pth.example_templ_path))
        self.inflection_templ = Template(filename=str(pth.inflection_templ_path))
        self.family_root_templ = Template(filename=str(pth.family_root_templ_path))
        self.family_word_templ = Template(filename=str(pth.family_word_templ_path))
        self.family_compound_templ = Template(filename=str(pth.family_compound_templ_path))
        self.family_set_templ = Template(filename=str(pth.family_set_templ_path))
        self.frequency_templ = Template(filename=str(pth.frequency_templ_path))
        self.feedback_templ = Template(filename=str(pth.feedback_templ_path))

        with open(pth.dpd_css_path) as f:
            dpd_css = f.read()

        self.dpd_css = css_minify(dpd_css)

        with open(pth.buttons_js_path) as f:
            button_js = f.read()
        self.button_js = js_minify(button_js)

def get_family_compounds_for_pali_word(i: PaliWord) -> List[FamilyCompound]:
    db_session = object_session(i)
    if db_session is None:
        raise Exception("No db_session")

    if i.family_compound:
        fc = db_session.query(
            FamilyCompound
        ).filter(
            FamilyCompound.compound_family.in_(i.family_compound_list),
        ).all()

        # sort by order of the  family compound list
        word_order = i.family_compound_list
        fc = sorted(fc, key=lambda x: word_order.index(x.compound_family))

    else:
        fc = db_session.query(
            FamilyCompound
        ).filter(
            FamilyCompound.compound_family == i.pali_clean
        ).all()

    # Make sure it's not a lazy-loaded iterable.
    fc = list(fc)

    return fc

def get_family_set_for_pali_word(i: PaliWord) -> List[FamilySet]:
    db_session = object_session(i)
    if db_session is None:
        raise Exception("No db_session")

    fs = db_session.query(
        FamilySet
    ).filter(
        FamilySet.set.in_(i.family_set_list)
    ).all()

    # sort by order of the  family set list
    word_order = i.family_set_list
    fs = sorted(fs, key=lambda x: word_order.index(x.set))

    # Make sure it's not a lazy-loaded iterable.
    fs = list(fs)

    return fs

PaliWordDbRowItems = Tuple[PaliWord, DerivedData, FamilyRoot, FamilyWord]

class PaliWordDbParts(TypedDict):
   pali_word: PaliWord
   pali_root: PaliRoot
   derived_data: DerivedData
   family_root: FamilyRoot
   family_word: FamilyWord
   family_compounds: List[FamilyCompound]
   family_set: List[FamilySet]

class PaliWordRenderData(TypedDict):
    pth: ProjectPaths
    word_templates: PaliWordTemplates
    sandhi_contractions: SandhiContractions
    cf_set: Set[str]
    make_link: bool

def render_pali_word_dpd_html(db_parts: PaliWordDbParts,
                              render_data: PaliWordRenderData) -> Tuple[RenderResult, RenderedSizes]:
    rd = render_data
    size_dict = default_rendered_sizes()

    i: PaliWord = db_parts["pali_word"]
    rt: PaliRoot = db_parts["pali_root"]
    dd: DerivedData = db_parts["derived_data"]
    fr: FamilyRoot = db_parts["family_root"]
    fw: FamilyWord = db_parts["family_word"]
    fc: List[FamilyCompound] = db_parts["family_compounds"]
    fs: List[FamilySet] = db_parts["family_set"]

    tt = rd['word_templates']
    pth = rd['pth']
    sandhi_contractions = rd['sandhi_contractions']

    # replace \n with html line break
    if i.meaning_1:
        i.meaning_1 = i.meaning_1.replace("\n", "<br>")
    if i.sanskrit:
        i.sanskrit = i.sanskrit.replace("\n", "<br>")
    if i.phonetic:
        i.phonetic = i.phonetic.replace("\n", "<br>")
    if i.compound_construction:
        i.compound_construction = i.compound_construction.replace("\n", "<br>")
    if i.commentary:
        i.commentary = i.commentary.replace("\n", "<br>")
    if i.link:
        i.link = i.link.replace("\n", "<br>")
    if i.sutta_1:
        i.sutta_1 = i.sutta_1.replace("\n", "<br>")
    if i.sutta_2:
        i.sutta_2 = i.sutta_2.replace("\n", "<br>")
    if i.example_1:
        i.example_1 = i.example_1.replace("\n", "<br>")
    if i.example_2:
        i.example_2 = i.example_2.replace("\n", "<br>")

    html: str = ""
    header = render_header_templ(pth, tt.dpd_css, tt.button_js, tt.header_templ)
    html += header
    size_dict["dpd_header"] += len(header)

    html += "<body>"

    summary = render_dpd_definition_templ(pth, i, tt.dpd_definition_templ)
    html += summary
    size_dict["dpd_summary"] += len(summary)

    button_box = render_button_box_templ(pth, i, rd['cf_set'], tt.button_box_templ)
    html += button_box
    size_dict["dpd_button_box"] += len(button_box)

    grammar = render_grammar_templ(pth, i, rt, tt.grammar_templ)
    html += grammar
    size_dict["dpd_grammar"] += len(grammar)

    example = render_example_templ(pth, i, rd['make_link'], tt.example_templ)
    html += example
    size_dict["dpd_example"] += len(example)

    inflection_table = render_inflection_templ(pth, i, dd, tt.inflection_templ)
    html += inflection_table
    size_dict["dpd_inflection_table"] += len(inflection_table)

    family_root = render_family_root_templ(pth, i, fr, tt.family_root_templ)
    html += family_root
    size_dict["dpd_family_root"] += len(family_root)

    family_word = render_family_word_templ(pth, i, fw, tt.family_word_templ)
    html += family_word
    size_dict["dpd_family_word"] += len(family_word)

    family_compound = render_family_compound_templ(
        pth, i, fc, rd['cf_set'], tt.family_compound_templ)
    html += family_compound
    size_dict["dpd_family_compound"] += len(family_compound)

    family_sets = render_family_set_templ(pth, i, fs, tt.family_set_templ)
    html += family_sets
    size_dict["dpd_family_sets"] += len(family_sets)

    frequency = render_frequency_templ(pth, i, dd, tt.frequency_templ)
    html += frequency
    size_dict["dpd_frequency"] += len(frequency)

    feedback = render_feedback_templ(pth, i, tt.feedback_templ)
    html += feedback
    size_dict["dpd_feedback"] += len(feedback)

    html += "</body></html>"
    html = minify(html)

    synonyms: List[str] = dd.inflections_list
    synonyms = add_niggahitas(synonyms)
    for synonym in synonyms:
        if synonym in sandhi_contractions:
            contractions = sandhi_contractions[synonym]["contractions"]
            synonyms.extend(contractions)
    synonyms += dd.sinhala_list
    synonyms += dd.devanagari_list
    synonyms += dd.thai_list
    synonyms += i.family_set_list
    synonyms += [str(i.id)]
    size_dict["dpd_synonyms"] += len(str(synonyms))

    res = RenderResult(
        word = i.pali_1,
        definition_html = html,
        definition_plain = "",
        synonyms = synonyms,
    )

    return (res, size_dict)

def generate_dpd_html(
        db_session: Session,
        pth: ProjectPaths,
        sandhi_contractions: SandhiContractions,
        cf_set: Set[str]) -> Tuple[List[RenderResult], RenderedSizes]:

    print("[green]generating dpd html")

    t0 = datetime.now()
    time_log(t0, "generate_dpd_html()", start_new=True)

    word_templates = PaliWordTemplates(pth)

    # check config
    if config_test("dictionary", "make_link", "yes"):
        make_link: bool = True
    else:
        make_link: bool = False

    dpd_data_list: List[RenderResult] = []

    dpd_db = db_session.query(
        PaliWord, DerivedData, FamilyRoot, FamilyWord
    ).outerjoin(
        DerivedData,
        PaliWord.id == DerivedData.id
    ).outerjoin(
        FamilyRoot,
        and_(
            PaliWord.root_key == FamilyRoot.root_id,
            PaliWord.family_root == FamilyRoot.root_family)
    ).outerjoin(
        FamilyWord,
        PaliWord.family_word == FamilyWord.word_family
    ).all()

    def _add_parts(i: PaliWordDbRowItems) -> PaliWordDbParts:
        pw: PaliWord
        dd: DerivedData
        fr: FamilyRoot
        fw: FamilyWord
        pw, dd, fr, fw = i

        return PaliWordDbParts(
            pali_word = pw,
            pali_root = pw.rt,
            derived_data = dd,
            family_root = fr,
            family_word = fw,
            family_compounds = get_family_compounds_for_pali_word(pw),
            family_set = get_family_set_for_pali_word(pw),
        )

    dpd_db_data = [_add_parts(i.tuple()) for i in dpd_db]

    time_log(t0, "db items collected")

    rendered_sizes: List[RenderedSizes] = []

    bip()

    num_logical_cores = psutil.cpu_count()

    batches: List[List[PaliWordDbParts]] = list_into_batches(dpd_db_data, num_logical_cores)

    processes: List[Process] = []
    manager = Manager()
    dpd_data_results_list: ListProxy = manager.list()
    rendered_sizes_results_list: ListProxy = manager.list()

    def _parse_batch(batch: List[PaliWordDbParts],
                     render_data: PaliWordRenderData,
                     dpd_data_results_list: ListProxy,
                     rendered_sizes_results_list: ListProxy,
                     batch_idx: int):

        res: List[Tuple[RenderResult, RenderedSizes]] = \
            [render_pali_word_dpd_html(i, render_data) for i in batch]

        for i, j in res:
            dpd_data_results_list.append(i)
            rendered_sizes_results_list.append(j)

        first_word = batch[0]["pali_word"]

        print(f"Batch {batch_idx}: done, from {first_word.pali_1}")

    render_data = PaliWordRenderData(
        pth = pth,
        word_templates = word_templates,
        sandhi_contractions = sandhi_contractions,
        cf_set = cf_set,
        make_link = make_link,
    )

    for batch_idx, batch in enumerate(batches):
        p = Process(target=_parse_batch, args=(batch,
                                               render_data,
                                               dpd_data_results_list,
                                               rendered_sizes_results_list,
                                               batch_idx,))

        w = batch[0]["pali_word"]
        print(f"Batch {batch_idx}: start, len {len(batch):>10,}, from {w.pali_1}")

        p.start()
        processes.append(p)

    for p in processes:
        p.join()

    time_log(t0, "batches finished")

    dpd_data_list = list(dpd_data_results_list)
    time_log(t0, "dpd_data_list to list")

    rendered_sizes = list(rendered_sizes_results_list)
    time_log(t0, "rendered_sizes to list")

    total_sizes = sum_rendered_sizes(rendered_sizes)

    time_log(t0, "return")

    return dpd_data_list, total_sizes


def render_header_templ(
        __pth__: ProjectPaths,
        css: str,
        js: str,
        header_templ: Template
) -> str:
    """render the html header with css and js"""

    return str(header_templ.render(css=css, js=js))


def render_dpd_definition_templ(
        __pth__: ProjectPaths,
        i: PaliWord,
        dpd_definition_templ: Template
) -> str:
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
    if i.plus_case is not None and i.plus_case:
        plus_case: str = i.plus_case

    meaning = make_meaning_html(i)
    summary = summarize_constr(i)
    complete = degree_of_completion(i)

    return str(
        dpd_definition_templ.render(
            i=i,
            pos=pos,
            plus_case=plus_case,
            meaning=meaning,
            summary=summary,
            complete=complete))


def render_button_box_templ(
        __pth__: ProjectPaths,
        i: PaliWord,
        cf_set: Set[str],
        button_box_templ: Template
) -> str:
    """render buttons for each section of the dictionary"""

    button_html = (
        '<a class="button" '
        'href="javascript:void(0);" '
        'onclick="button_click(this)" '
        'data-target="{target}">{name}</a>')

    # grammar_button
    if i.meaning_1:
        grammar_button = button_html.format(
            target=f"grammar_{i.pali_1_}", name="grammar")
    else:
        grammar_button = ""

    # example_button
    if i.meaning_1 and i.example_1 and not i.example_2:
        example_button = button_html.format(
            target=f"example_{i.pali_1_}", name="example")
    else:
        example_button = ""

    # examples_button
    if i.meaning_1 and i.example_1 and i.example_2:
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
    if i.family_root:
        root_family_button = button_html.format(
            target=f"root_family_{i.pali_1_}", name="root family")
    else:
        root_family_button = ""

    # word_family_button
    if i.family_word:
        word_family_button = button_html.format(
            target=f"word_family_{i.pali_1_}", name="word family")
    else:
        word_family_button = ""

    # compound_family_button
    if (
        i.meaning_1 and
        (
            i.family_compound or
            i.pali_clean in cf_set
        )
    ):

        if i.family_compound is not None and " " not in i.family_compound:
            compound_family_button = button_html.format(
                target=f"compound_family_{i.pali_1_}", name="compound family")

        else:
            compound_family_button = button_html.format(
                target=f"compound_family_{i.pali_1_}", name="compound familes")

    else:
        compound_family_button = ""

    # set_family_button
    if (i.meaning_1 and
            i.family_set):

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


def render_grammar_templ(
        __pth__: ProjectPaths,
        i: PaliWord,
        rt: PaliRoot,
        grammar_templ: Template
) -> str:
    """html table of grammatical information"""

    if i.meaning_1 is not None and i.meaning_1:
        if i.construction is not None and i.construction:
            i.construction = i.construction.replace("\n", "<br>")
        else:
            i.construction = ""

        grammar = i.grammar
        if i.neg:
            grammar += f", {i.neg}"
        if i.verb:
            grammar += f", {i.verb}"
        if i.trans:
            grammar += f", {i.trans}"
        if i.plus_case:
            grammar += f" ({i.plus_case})"

        meaning = f"<b>{make_meaning_html(i)}</b>"

        return str(
            grammar_templ.render(
                i=i,
                rt=rt,
                grammar=grammar,
                meaning=meaning,
                today=TODAY))

    else:
        return ""


def render_example_templ(
        __pth__: ProjectPaths,
        i: PaliWord,
        make_link: bool,
        example_templ: Template
) -> str:
    """render sutta examples html"""

    if i.meaning_1 and i.example_1:
        return str(
            example_templ.render(
                i=i,
                make_link=make_link,
                today=TODAY))
    else:
        return ""


def render_inflection_templ(
        __pth__: ProjectPaths,
        i: PaliWord,
        dd: DerivedData,
        inflection_templ:Template
) -> str:
    """inflection or conjugation table"""

    if i.pos not in INDECLINABLES:
        return str(
            inflection_templ.render(
                i=i,
                table=dd.html_table,
                today=TODAY,
                declensions=DECLENSIONS,
                conjugations=CONJUGATIONS))
    else:
        return ""


def render_family_root_templ(
        __pth__: ProjectPaths,
        i: PaliWord,
        fr: FamilyRoot,
        family_root_templ
) -> str:
    """render html table of all words with the same prefix and root"""

    if fr is not None:
        if i.family_root:
            return str(
                family_root_templ.render(
                    i=i,
                    fr=fr,
                    today=TODAY))
        else:
            return ""
    else:
        return ""


def render_family_word_templ(
        __pth__: ProjectPaths,
        i: PaliWord,
        fw: FamilyWord,
        family_word_templ: Template
) -> str:
    """render html of all words which belong to the same family"""

    if i.family_word:
        return str(
            family_word_templ.render(
                i=i,
                fw=fw,
                today=TODAY))
    else:
        return ""


def render_family_compound_templ(
        __pth__: ProjectPaths,
        i: PaliWord,
        fc: List[FamilyCompound],
        cf_set: Set[str],
        family_compound_templ: Template
) -> str:
    """render html table of all words containing the same compound"""

    if (i.meaning_1 and
        (i.family_compound or
            i.pali_clean in cf_set)):

        return str(
            family_compound_templ.render(
                i=i,
                fc=fc,
                today=TODAY))
    else:
        return ""


def render_family_set_templ(
        __pth__: ProjectPaths,
        i: PaliWord,
        fs: List[FamilySet],
        family_set_templ: Template
) -> str:
    """render html table of all words belonging to the same set"""

    if (i.meaning_1 and
            i.family_set):

        if len(i.family_set_list) > 0:

            return str(
                family_set_templ.render(
                    i=i,
                    fs=fs,
                    today=TODAY))
        else:
            return ""
    else:
        return ""


def render_frequency_templ(
        __pth__: ProjectPaths,
        i: PaliWord,
        dd: DerivedData,
        frequency_templ: Template
) -> str:
    """render html tempalte of freqency table"""

    if i.pos not in EXCLUDE_FROM_FREQ:

        return str(
            frequency_templ.render(
                i=i,
                dd=dd,
                today=TODAY))
    else:
        return ""


def render_feedback_templ(
        __pth__: ProjectPaths,
        i: PaliWord,
        feedback_templ: Template
) -> str:
    """render html of feedback template"""

    return str(
        feedback_templ.render(
            i=i,
            today=TODAY))
