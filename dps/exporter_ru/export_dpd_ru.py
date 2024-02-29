"""Compile HTML data for DpdHeadwords."""

import psutil

from sqlalchemy.sql import func


from css_html_js_minify import css_minify, js_minify
from mako.template import Template
from minify_html import minify
from multiprocessing.managers import ListProxy
from multiprocessing import Process, Manager
from rich import print
from typing import List, Set, TypedDict, Tuple


from sqlalchemy.orm.session import Session

# in the make_ru_dpd.sh it mentioned "export PYTHONPATH=/home/deva/Documents/dpd-db/exporter:$PYTHONPATH"
from helpers import TODAY # type: ignore
from export_dpd import render_header_templ # type: ignore

from tools import time_log

from db.models import DpdHeadwords, FamilyIdiom
from db.models import DpdRoots
from db.models import FamilyCompound
from db.models import FamilyRoot
from db.models import FamilySet
from db.models import FamilyWord
from db.models import Russian

# from tools.configger import config_test
from tools.exporter_functions import get_family_compounds, get_family_idioms
from tools.exporter_functions import get_family_set
from tools.meaning_construction import make_meaning_html
# from tools.meaning_construction import make_grammar_line
from tools.meaning_construction import summarize_construction
from tools.meaning_construction import degree_of_completion
from tools.niggahitas import add_niggahitas
from tools.paths import ProjectPaths
from dps.tools.paths_dps import DPSPaths
from tools.pos import CONJUGATIONS
from tools.pos import DECLENSIONS
from tools.sandhi_contraction import SandhiContractions
from tools.superscripter import superscripter_uni
from tools.tic_toc import bip, bop
from tools.utils import RenderResult, RenderedSizes, default_rendered_sizes, list_into_batches, sum_rendered_sizes

from dps.tools.tools_for_dps_exporter import make_ru_meaning_html, replace_abbreviations, ru_make_grammar_line

class RuDpdHeadwordsTemplates:
    def __init__(self, pth: ProjectPaths, dpspth: DPSPaths):
        self.header_templ = Template(filename=str(pth.header_templ_path))
        self.dpd_ru_definition_templ = Template(filename=str(dpspth.dpd_ru_definition_templ_path))
        self.button_box_templ = Template(filename=str(dpspth.button_box_templ_path))
        self.grammar_templ = Template(filename=str(dpspth.grammar_templ_path))
        self.example_templ = Template(filename=str(dpspth.example_templ_path))
        self.inflection_templ = Template(filename=str(dpspth.inflection_templ_path))
        self.family_root_templ = Template(filename=str(dpspth.family_root_templ_path))
        self.family_word_templ = Template(filename=str(dpspth.family_word_templ_path))
        self.family_compound_templ = Template(filename=str(dpspth.family_compound_templ_path))
        self.family_idiom_templ = Template(filename=str(dpspth.family_idiom_templ_path))
        self.family_set_templ = Template(filename=str(dpspth.family_set_templ_path))
        self.frequency_templ = Template(filename=str(dpspth.frequency_templ_path))
        self.feedback_templ = Template(filename=str(dpspth.feedback_templ_path))

        with open(dpspth.dpd_css_path) as f:
            dpd_css = f.read()

        self.dpd_css = css_minify(dpd_css)

        with open(pth.buttons_js_path) as f:
            button_js = f.read()
        self.button_js = js_minify(button_js)

DpdHeadwordsDbRowItems = Tuple[DpdHeadwords, FamilyRoot, FamilyWord, Russian]

class RuDpdHeadwordsDbParts(TypedDict):
   pali_word: DpdHeadwords
   pali_root: DpdRoots
   ru: Russian
   family_root: FamilyRoot
   family_word: FamilyWord
   family_compounds: List[FamilyCompound]
   family_idioms: List[FamilyIdiom]
   family_set: List[FamilySet]

class RuDpdHeadwordsRenderData(TypedDict):
    pth: ProjectPaths
    word_templates: RuDpdHeadwordsTemplates
    sandhi_contractions: SandhiContractions
    cf_set: Set[str]
    idioms_set: Set[str]

def render_pali_word_dpd_html(
        db_parts: RuDpdHeadwordsDbParts,
        render_data: RuDpdHeadwordsRenderData) -> Tuple[RenderResult, RenderedSizes]:
    rd = render_data
    size_dict = default_rendered_sizes()

    i: DpdHeadwords = db_parts["pali_word"]
    rt: DpdRoots = db_parts["pali_root"]
    ru: Russian = db_parts["ru"]
    fr: FamilyRoot = db_parts["family_root"]
    fw: FamilyWord = db_parts["family_word"]
    fc: List[FamilyCompound] = db_parts["family_compounds"]
    fi: List[FamilyIdiom] = db_parts["family_idioms"]
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

    summary = render_dpd_ru_definition_templ(
        pth, i, ru, tt.dpd_ru_definition_templ)
    html += summary
    size_dict["dpd_summary"] += len(summary)

    button_box = render_button_box_templ(
        pth, i, rd['cf_set'], rd['idioms_set'], tt.button_box_templ)
    html += button_box
    size_dict["dpd_button_box"] += len(button_box)

    if i.needs_grammar_button:
        grammar = render_grammar_templ(pth, i, rt, ru, tt.grammar_templ)
        html += grammar
        size_dict["dpd_grammar"] += len(grammar)

    if i.needs_example_button or i.needs_examples_button:
        example = render_example_templ(pth, i, tt.example_templ)
        html += example
        size_dict["dpd_example"] += len(example)

    if i.needs_conjugation_button or i.needs_declension_button:
        inflection_table = render_inflection_templ(pth, i, tt.inflection_templ)
        html += inflection_table
        size_dict["dpd_inflection_table"] += len(inflection_table)

    if i.needs_root_family_button:
        family_root = render_family_root_templ(pth, i, fr, tt.family_root_templ)
        html += family_root
        size_dict["dpd_family_root"] += len(family_root)

    if i.needs_word_family_button:
        family_word = render_family_word_templ(pth, i, fw, tt.family_word_templ)
        html += family_word
        size_dict["dpd_family_word"] += len(family_word)

    if i.needs_compound_family_button or i.needs_compound_families_button:
        family_compound = render_family_compound_templ(
            pth, i, fc, rd['cf_set'], tt.family_compound_templ)
        html += family_compound
        size_dict["dpd_family_compound"] += len(family_compound)

    if i.needs_idioms_button:
        family_idiom = render_family_idioms_templ(
            pth, i, fi, rd['idioms_set'], tt.family_idiom_templ)
        html += family_idiom
        size_dict["dpd_family_idiom"] += len(family_idiom)

    if i.needs_set_button or i.needs_sets_button:
        family_sets = render_family_set_templ(pth, i, fs, tt.family_set_templ)
        html += family_sets
        size_dict["dpd_family_sets"] += len(family_sets)

    if i.needs_frequency_button:
        frequency = render_frequency_templ(pth, i, tt.frequency_templ)
        html += frequency
        size_dict["dpd_frequency"] += len(frequency)

    feedback = render_feedback_templ(pth, i, tt.feedback_templ)
    html += feedback
    size_dict["dpd_feedback"] += len(feedback)

    html += "</body></html>"
    html = minify(html)

    synonyms: List[str] = i.inflections_list
    synonyms = add_niggahitas(synonyms)
    for synonym in synonyms:
        if synonym in sandhi_contractions:
            contractions = sandhi_contractions[synonym]["contractions"]
            for contraction in contractions:
                if "'" in contraction:
                    synonyms.append(contraction)
    synonyms += i.family_set_list
    synonyms += [str(i.id)]

    size_dict["dpd_synonyms"] += len(str(synonyms))

    res = RenderResult(
        word = i.lemma_1,
        definition_html = html,
        definition_plain = "",
        synonyms = synonyms,
    )

    return (res, size_dict)

def generate_dpd_html(
        db_session: Session,
        pth: ProjectPaths,
        dpspth: DPSPaths,
        sandhi_contractions: SandhiContractions,
        cf_set: Set[str],
        idioms_set: set[str]
        ) -> Tuple[List[RenderResult], RenderedSizes]:
    
    time_log.log("generate_dpd_ru_html()")

    print("[green]generating dpd ru html")
    bip()

    word_templates = RuDpdHeadwordsTemplates(pth, dpspth)

    dpd_data_list: List[RenderResult] = []

    pali_words_count = db_session \
        .query(func.count(DpdHeadwords.id)) \
        .join(Russian, DpdHeadwords.id == Russian.id) \
        .filter(Russian.id.isnot(None)) \
        .scalar()
        
    # If the work items per loop are too high, low-memory systems will slow down
    # when multi-threading.
    #
    # Setting the threshold to 9 GB to make sure 8 GB systems are covered.
    low_mem_threshold = 9*1024*1024*1024
    mem = psutil.virtual_memory()
    if mem.total < low_mem_threshold:
        limit = 2000
    else:
        limit = 5000

    offset = 0

    manager = Manager()
    dpd_data_results_list: ListProxy = manager.list()
    rendered_sizes_results_list: ListProxy = manager.list()
    num_logical_cores = psutil.cpu_count()
    print(f"num_logical_cores {num_logical_cores}")

    time_log.log("while offset <= pali_words_count:")

    while offset <= pali_words_count:

        dpd_db = db_session.query(
            DpdHeadwords, FamilyRoot, FamilyWord, Russian
        ).outerjoin(
            Russian,
            DpdHeadwords.id == Russian.id
        ).outerjoin(
            FamilyRoot,
            DpdHeadwords.root_family_key == FamilyRoot.root_family_key
        ).outerjoin(
            FamilyWord,
            DpdHeadwords.family_word == FamilyWord.word_family
        ).filter(
            Russian.id.isnot(None)
        ).limit(limit).offset(offset).all()

        def _add_parts(i: DpdHeadwordsDbRowItems) -> RuDpdHeadwordsDbParts:
            pw: DpdHeadwords
            fr: FamilyRoot
            fw: FamilyWord
            ru: Russian
            pw, fr, fw, ru = i

            return RuDpdHeadwordsDbParts(
                pali_word = pw,
                pali_root = pw.rt,
                ru = ru,
                family_root = fr,
                family_word = fw,
                family_compounds = get_family_compounds(pw),
                family_idioms = get_family_idioms(pw),
                family_set = get_family_set(pw),
            )

        dpd_db_data = [_add_parts(i.tuple()) for i in dpd_db]

        rendered_sizes: List[RenderedSizes] = []

        batches: List[List[RuDpdHeadwordsDbParts]] = list_into_batches(dpd_db_data, num_logical_cores)

        processes: List[Process] = []

        render_data = RuDpdHeadwordsRenderData(
            pth = pth,
            word_templates = word_templates,
            sandhi_contractions = sandhi_contractions,
            cf_set = cf_set,
            idioms_set = idioms_set,
        )

        def _parse_batch(batch: List[RuDpdHeadwordsDbParts]):
            res: List[Tuple[RenderResult, RenderedSizes]] = \
                [render_pali_word_dpd_html(i, render_data) for i in batch]

            for i, j in res:
                dpd_data_results_list.append(i)
                rendered_sizes_results_list.append(j)

        for batch in batches:
            p = Process(target=_parse_batch, args=(batch,))

            p.start()
            processes.append(p)

        for p in processes:
            p.join()

        offset += limit

    time_log.log("dpd_data_list = list...")
    dpd_data_list = list(dpd_data_results_list)

    time_log.log("rendered_sizes = list...")
    rendered_sizes = list(rendered_sizes_results_list)

    time_log.log("total_sizes = sum_ren...")
    total_sizes = sum_rendered_sizes(rendered_sizes)

    time_log.log("generate_dpd_html() return")
    
    print(f"html render time: {bop()}")
    return dpd_data_list, total_sizes



def render_dpd_ru_definition_templ(
        pth: ProjectPaths,
        i: DpdHeadwords,
        ru: Russian,
        dpd_ru_definition_templ: Template,
) -> str:
    """render the definition of a word's most relevant information:
    1. pos
    2. case
    3 meaning
    4. summary
    5. degree of completition"""

    # pos replace with ru
    pos: str = replace_abbreviations(i.pos, pth)

    # plus_case
    plus_case: str = ""
    if i.plus_case is not None and i.plus_case:
        plus_case: str = replace_abbreviations(i.plus_case, pth)

    # meaning
    if ru:
        ru_meaning = make_ru_meaning_html(i, ru)
        if ru_meaning:
            meaning = ru_meaning
        else:
            meaning = make_meaning_html(i)
    else:
        meaning = make_meaning_html(i)

    machine_sing = False

    if (
        ru
        and not ru.ru_meaning
        and ru.ru_meaning_raw
    ):
        machine_sing = True
        

    summary = summarize_construction(i)
    complete = degree_of_completion(i)

    # id
    id: int = i.id

    return str(
        dpd_ru_definition_templ.render(
            i=i,
            pos=pos,
            plus_case=plus_case,
            meaning=meaning,
            summary=summary,
            complete=complete,
            id=id,
            machine_sing=machine_sing,
            today=TODAY
            )
        )


def render_button_box_templ(
        pth: ProjectPaths,
        i: DpdHeadwords,
        cf_set: Set[str],
        idioms_set: Set[str],
        button_box_templ: Template
) -> str:
    """render buttons for each section of the dictionary"""

    button_html = (
        '<a class="button_ru" '
        'href="javascript:void(0);" '
        'onclick="button_click(this)" '
        'data-target="{target}">{name}</a>')

    # grammar_button
    if i.needs_grammar_button:
        grammar_button = button_html.format(
            target=f"ru_grammar_{i.lemma_1_}", name="грамматика")
    else:
        grammar_button = ""

    # example_button
    if i.needs_example_button:
        example_button = button_html.format(
            target=f"ru_example_{i.lemma_1_}", name="пример")
    else:
        example_button = ""

    # examples_button
    if i.needs_examples_button:
        examples_button = button_html.format(
            target=f"ru_examples_{i.lemma_1_}", name="примеры")
    else:
        examples_button = ""

    # conjugation_button
    if i.needs_conjugation_button:
        conjugation_button = button_html.format(
            target=f"ru_conjugation_{i.lemma_1_}", name="спряжения")
    else:
        conjugation_button = ""

    # declension_button
    if i.needs_declension_button:
        declension_button = button_html.format(
            target=f"ru_declension_{i.lemma_1_}", name="склонения")
    else:
        declension_button = ""

    # root_family_button
    if i.needs_root_family_button:
        root_family_button = button_html.format(
            target=f"ru_root_family_{i.lemma_1_}", name="семья корня")
    else:
        root_family_button = ""

    # word_family_button
    if i.needs_word_family_button:
        word_family_button = button_html.format(
            target=f"ru_word_family_{i.lemma_1_}", name="семья слова")
    else:
        word_family_button = ""

    # compound_family_button
    if i.needs_compound_family_button:
        compound_family_button = button_html.format(
            target=f"ru_compound_family_{i.lemma_1_}", name="семья составного")

    elif i.needs_compound_families_button:
        compound_family_button = button_html.format(
            target=f"ru_compound_families_{i.lemma_1_}", name="семья составных")
    else:
        compound_family_button = ""

    # idioms button
    if i.needs_idioms_button:
        idioms_button = button_html.format(
            target=f"ru_idioms_{i.lemma_1_}", name="идиомы")
    else:
        idioms_button = ""

    # set_family_button
    if i.needs_set_button:
        set_family_button = button_html.format(
            target=f"ru_set_family_{i.lemma_1_}", name="группа")
    elif i.needs_sets_button:
        set_family_button = button_html.format(
            target=f"ru_set_families_{i.lemma_1_}", name="группы")
    else:
        set_family_button = ""

    # frequency_button
    if i.needs_frequency_button:
        frequency_button = button_html.format(
            target=f"ru_frequency_{i.lemma_1_}", name="частота")
    else:
        frequency_button = ""

    # feedback_button
    feedback_button = button_html.format(
        target=f"ru_feedback_{i.lemma_1_}", name="о словаре")

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
            idioms_button=idioms_button,
            set_family_button=set_family_button,
            frequency_button=frequency_button,
            feedback_button=feedback_button))


def render_grammar_templ(
        pth: ProjectPaths,
        i: DpdHeadwords,
        rt: DpdRoots,
        ru: Russian,
        grammar_templ: Template
) -> str:
    """html table of grammatical information"""

    if (i.meaning_1 is not None and i.meaning_1):
        if i.construction is not None and i.construction:
            i.construction = i.construction.replace("\n", "<br>")
        else:
            i.construction = ""

    grammar = ru_make_grammar_line(i, pth)

    meaning = f"{make_meaning_html(i)}"

    return str(
        grammar_templ.render(
            i=i,
            rt=rt,
            ru=ru,
            grammar=grammar,
            meaning=meaning,
            today=TODAY))


def render_example_templ(
        pth: ProjectPaths,
        i: DpdHeadwords,
        example_templ: Template
) -> str:
    """render sutta examples html"""

    return str(
        example_templ.render(
            i=i,
            today=TODAY))


def render_inflection_templ(
        pth: ProjectPaths,
        i: DpdHeadwords,
        inflection_templ:Template
) -> str:
    """inflection or conjugation table"""

    return str(
        inflection_templ.render(
            i=i,
            table=i.inflections_html,
            today=TODAY,
            declensions=DECLENSIONS,
            conjugations=CONJUGATIONS))


def render_family_root_templ(
        pth: ProjectPaths,
        i: DpdHeadwords,
        fr: FamilyRoot,
        family_root_templ
) -> str:
    """render html table of all words with the same prefix and root"""

    return str(
        family_root_templ.render(
            i=i,
            fr=fr,
            today=TODAY))


def render_family_word_templ(
        pth: ProjectPaths,
        i: DpdHeadwords,
        fw: FamilyWord,
        family_word_templ: Template
) -> str:
    """render html of all words which belong to the same family"""

    return str(
        family_word_templ.render(
            i=i,
            fw=fw,
            today=TODAY))


def render_family_compound_templ(
        pth: ProjectPaths,
        i: DpdHeadwords,
        fc: List[FamilyCompound],
        cf_set: Set[str],
        family_compound_templ: Template
) -> str:
    """render html table of all words containing the same compound"""

    return str(
        family_compound_templ.render(
            i=i,
            fc=fc,
            superscripter_uni=superscripter_uni,
            today=TODAY))


def render_family_idioms_templ(
        pth: ProjectPaths,
        i: DpdHeadwords,
        fi: List[FamilyIdiom],
        idioms_set: Set[str],
        family_idioms_template: Template
) -> str:
    """render html table of all words containing the same compound"""

    return str(
        family_idioms_template.render(
            i=i,
            fi=fi,
            superscripter_uni=superscripter_uni,
            today=TODAY))


def render_family_set_templ(
        pth: ProjectPaths,
        i: DpdHeadwords,
        fs: List[FamilySet],
        family_set_templ: Template
) -> str:
    """render html table of all words belonging to the same set"""

    return str(
        family_set_templ.render(
            i=i,
            fs=fs,
            superscripter_uni=superscripter_uni,
            today=TODAY))


def render_frequency_templ(
        pth: ProjectPaths,
        i: DpdHeadwords,
        frequency_templ: Template
) -> str:
    """render html tempalte of freqency table"""

    return str(
        frequency_templ.render(
            i=i,
            today=TODAY))


def render_feedback_templ(
        pth: ProjectPaths,
        i: DpdHeadwords,
        feedback_templ: Template
) -> str:
    """render html of feedback template"""

    return str(
        feedback_templ.render(
            i=i,
            today=TODAY))
