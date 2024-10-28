"""Compile HTML data for DpdHeadword."""

import psutil

from sqlalchemy.sql import func


# from css_html_js_minify import css_minify, js_minify
from mako.template import Template
from minify_html import minify
from multiprocessing.managers import ListProxy
from multiprocessing import Process, Manager
from typing import List, Set, TypedDict, Tuple, Union

from sqlalchemy.orm.session import Session

from exporter.goldendict.helpers import TODAY

from db.models import DpdHeadword
from db.models import DpdRoot
from db.models import FamilyCompound
from db.models import FamilyIdiom
from db.models import FamilyRoot
from db.models import FamilySet
from db.models import FamilyWord
from db.models import Russian
from db.models import SBS

from tools.configger import config_test
from tools.date_and_time import year_month_day_dash
from tools.exporter_functions import get_family_compounds, get_family_idioms, get_family_set
from tools.goldendict_exporter import DictEntry
from tools.meaning_construction import make_meaning_combo_html, make_grammar_line
from tools.meaning_construction import summarize_construction, degree_of_completion
from tools.niggahitas import add_niggahitas
from tools.paths import ProjectPaths
from tools.pos import CONJUGATIONS, DECLENSIONS, INDECLINABLES
from tools.printer import p_counter, p_green_title
from tools.sandhi_contraction import SandhiContractions
from tools.superscripter import superscripter_uni
from tools.utils import RenderedSizes, default_rendered_sizes, list_into_batches
from tools.utils import sum_rendered_sizes, squash_whitespaces

from exporter.goldendict.ru_components.tools.paths_ru import RuPaths
from exporter.goldendict.ru_components.tools.tools_for_ru_exporter import make_ru_meaning_html, ru_replace_abbreviations
from exporter.goldendict.ru_components.tools.tools_for_ru_exporter import replace_english, ru_make_grammar_line, read_set_ru_from_tsv

class DpdHeadwordTemplates:
    def __init__(self, paths: Union[ProjectPaths, RuPaths], lang):
        self.paths = paths
        self.lang = lang
        self.header_templ = Template(filename=str(paths.dpd_header_templ_path))
        self.dpd_definition_templ = Template(filename=str(paths.dpd_definition_templ_path))
        self.button_box_templ = Template(filename=str(paths.button_box_templ_path))
        self.grammar_templ = Template(filename=str(paths.grammar_templ_path))
        self.example_templ = Template(filename=str(paths.example_templ_path))
        self.sbs_example_templ = Template(filename=str(paths.sbs_example_templ_path))
        self.inflection_templ = Template(filename=str(paths.inflection_templ_path))
        self.family_root_templ = Template(filename=str(paths.family_root_templ_path))
        self.family_word_templ = Template(filename=str(paths.family_word_templ_path))
        self.family_compound_templ = Template(filename=str(paths.family_compound_templ_path))
        self.family_idiom_templ = Template(filename=str(paths.family_idiom_templ_path))
        self.family_set_templ = Template(filename=str(paths.family_set_templ_path))
        self.frequency_templ = Template(filename=str(paths.frequency_templ_path))
        self.feedback_templ = Template(filename=str(paths.feedback_templ_path))

        self.dpd_css = ""
        self.button_js = ""

DpdHeadwordDbRowItems = Tuple[DpdHeadword, FamilyRoot, FamilyWord, SBS, Russian]

class DpdHeadwordDbParts(TypedDict):
    pali_word: DpdHeadword
    pali_root: DpdRoot
    sbs: SBS
    ru: Russian
    family_root: FamilyRoot
    family_word: FamilyWord
    family_compounds: List[FamilyCompound]
    family_idioms: List[FamilyIdiom]
    family_set: List[FamilySet]

class DpdHeadwordRenderData(TypedDict):
    pth: Union[ProjectPaths, RuPaths]
    word_templates: DpdHeadwordTemplates
    sandhi_contractions: SandhiContractions
    cf_set: Set[str]
    idioms_set: Set[str]
    make_link: bool
    show_id: bool
    show_ebt_count: bool
    show_sbs_data: bool
    show_ru_data: bool


def render_pali_word_dpd_html(
        db_parts: DpdHeadwordDbParts,
        render_data: DpdHeadwordRenderData,
        lang="en",
        extended_synonyms=False, 
        show_sbs_data=False,
        show_ru_data=False,
) -> Tuple[DictEntry, RenderedSizes]:
    rd = render_data
    size_dict = default_rendered_sizes()

    i: DpdHeadword = db_parts["pali_word"]
    rt: DpdRoot = db_parts["pali_root"]
    sbs: SBS = db_parts["sbs"]
    ru: Russian = db_parts["ru"]
    fr: FamilyRoot = db_parts["family_root"]
    fw: FamilyWord = db_parts["family_word"]
    fc: List[FamilyCompound] = db_parts["family_compounds"]
    fi: List[FamilyIdiom] = db_parts["family_idioms"]
    fs: List[FamilySet] = db_parts["family_set"]
    date: str = year_month_day_dash()

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
    if i.notes:
        i.notes = i.notes.replace("\n", "<br>")
    if show_sbs_data and sbs:
        if sbs.sbs_sutta_1:
            sbs.sbs_sutta_1 = sbs.sbs_sutta_1.replace("\n", "<br>")
        if sbs.sbs_sutta_2:
            sbs.sbs_sutta_2 = sbs.sbs_sutta_2.replace("\n", "<br>")
        if sbs.sbs_sutta_3:
            sbs.sbs_sutta_3 = sbs.sbs_sutta_3.replace("\n", "<br>")
        if sbs.sbs_sutta_4:
            sbs.sbs_sutta_4 = sbs.sbs_sutta_4.replace("\n", "<br>")
        if sbs.sbs_example_1:
            sbs.sbs_example_1 = sbs.sbs_example_1.replace("\n", "<br>")
        if sbs.sbs_example_2:
            sbs.sbs_example_2 = sbs.sbs_example_2.replace("\n", "<br>")
        if sbs.sbs_example_3:
            sbs.sbs_example_3 = sbs.sbs_example_3.replace("\n", "<br>")
        if sbs.sbs_example_4:
            sbs.sbs_example_4 = sbs.sbs_example_4.replace("\n", "<br>")

    html: str = ""
    html += "<body>"

    summary = render_dpd_definition_templ(
        pth, i, tt.dpd_definition_templ, sbs, ru, rd['make_link'], rd['show_id'], rd['show_ebt_count'], rd['show_sbs_data'], lang)
    html += summary
    size_dict["dpd_summary"] += len(summary)

    button_box = render_button_box_templ(
        pth, i, sbs, rd['cf_set'], rd['idioms_set'], tt.button_box_templ, lang, rd['show_sbs_data'])
    html += button_box
    size_dict["dpd_button_box"] += len(button_box)

    if i.needs_grammar_button or show_sbs_data:
        grammar = render_grammar_templ(pth, i, rt, sbs, ru, tt.grammar_templ, lang, rd['show_sbs_data'], rd['show_ru_data'])
        html += grammar
        size_dict["dpd_grammar"] += len(grammar)

    if i.needs_example_button or i.needs_examples_button:
        example = render_example_templ(pth, i, tt.example_templ, rd['make_link'])
        html += example
        size_dict["dpd_example"] += len(example)

    if i.needs_conjugation_button or i.needs_declension_button:
        inflection_table = render_inflection_templ(pth, i, tt.inflection_templ, lang)
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
        frequency = render_frequency_templ(pth, i, tt.frequency_templ, lang)
        html += frequency
        size_dict["dpd_frequency"] += len(frequency)

    if show_sbs_data and sbs:
        sbs_example = render_sbs_example_templ(pth, i, sbs, tt.sbs_example_templ, rd['make_link'])
        html += sbs_example
        size_dict["sbs_example"] += len(sbs_example)

    feedback = render_feedback_templ(pth, i, tt.feedback_templ)
    html += feedback
    size_dict["dpd_feedback"] += len(feedback)
    
    html += "</body></html>"

    header = str(tt.header_templ.render(i=i, date=date))
    size_dict["dpd_header"] += len(header)
    html = squash_whitespaces(header) + minify(html)

    synonyms: List[str] = i.inflections_list_all # include api ca eva iti
    synonyms = add_niggahitas(synonyms)
    for synonym in synonyms:
        if synonym in sandhi_contractions:
            contractions = sandhi_contractions[synonym]["contractions"]
            for contraction in contractions:
                if "'" in contraction:
                    synonyms.append(contraction)
    synonyms += i.inflections_sinhala_list
    synonyms += i.inflections_devanagari_list
    synonyms += i.inflections_thai_list
    synonyms += i.family_set_list
    if lang == "ru" or show_ru_data:
        set_ru_dict = read_set_ru_from_tsv()
        ru_set_list = []
        for english_word in i.family_set_list:
            if english_word in set_ru_dict:
                ru_set_list.append(set_ru_dict[english_word])
        synonyms += ru_set_list
    synonyms += [str(i.id)]


    if extended_synonyms:
        # Split i.lemma_clean only if it contains a space
        if ' ' in i.lemma_clean:
            words = i.lemma_clean.split(' ')
            synonyms.extend(words)
    

    size_dict["dpd_synonyms"] += len(str(synonyms))

    res = DictEntry(
        word = i.lemma_1,
        definition_html = html,
        definition_plain = "",
        synonyms = synonyms,
    )

    return (res, size_dict)

def generate_dpd_html(
        db_session: Session,
        pth: ProjectPaths,
        rupth: RuPaths,
        sandhi_contractions: SandhiContractions,
        cf_set: Set[str],
        idioms_set: set[str],
        make_link=False,
        show_sbs_data=False,
        show_ru_data=False,
        lang="en",
        data_limit:int = 0
) -> Tuple[List[DictEntry], RenderedSizes]:

    p_green_title("generating dpd html")

    if lang == "en":
        paths = pth
    elif lang == "ru":
        paths = rupth

    word_templates = DpdHeadwordTemplates(paths, lang)

    if config_test("dictionary", "extended_synonyms", "yes"):
        extended_synonyms: bool = True
    else:
        extended_synonyms: bool = False

    if config_test("dictionary", "show_id", "yes"):
        show_id: bool = True
    else:
        show_id: bool = False

    if config_test("dictionary", "show_ebt_count", "yes"):
        show_ebt_count: bool = True
    else:
        show_ebt_count: bool = False

    dpd_data_list: List[DictEntry] = []

    if lang == "en":
        pali_words_count = db_session \
            .query(func.count(DpdHeadword.id)) \
            .scalar()
    elif lang == "ru":
        pali_words_count = db_session \
            .query(func.count(DpdHeadword.id)) \
            .join(Russian, DpdHeadword.id == Russian.id) \
            .filter(Russian.id.isnot(None)) \
            .scalar()
    
    # limit the data size for testing purposes
    if data_limit != 0:
        pali_words_count = data_limit
        
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
    p_green_title(f"running with {num_logical_cores} cores")

    while offset <= pali_words_count:

        dpd_db_query = db_session.query(DpdHeadword, FamilyRoot, FamilyWord, SBS, Russian) \
            .outerjoin(FamilyRoot, DpdHeadword.root_family_key == FamilyRoot.root_family_key) \
            .outerjoin(FamilyWord, DpdHeadword.family_word == FamilyWord.word_family) \
            .outerjoin(Russian, DpdHeadword.id == Russian.id) \
            .outerjoin(SBS, DpdHeadword.id == SBS.id) \
            .order_by(DpdHeadword.lemma_1) \
        
        if lang == "ru":
            dpd_db_query = dpd_db_query.filter(
                    Russian.id.isnot(None)
                )

        dpd_db = dpd_db_query.limit(limit).offset(offset).all()

        def _add_parts(i: DpdHeadwordDbRowItems) -> DpdHeadwordDbParts:
            pw: DpdHeadword
            fr: FamilyRoot
            fw: FamilyWord
            sbs: SBS
            ru: Russian
            pw, fr, fw, sbs, ru = i

            return DpdHeadwordDbParts(
                pali_word = pw,
                pali_root = pw.rt,
                sbs = sbs,
                ru = ru,
                family_root = fr,
                family_word = fw,
                family_compounds = get_family_compounds(pw),
                family_idioms = get_family_idioms(pw),
                family_set = get_family_set(pw),
            )

        dpd_db_data = [_add_parts(i.tuple()) for i in dpd_db]

        rendered_sizes: List[RenderedSizes] = []

        batches: List[List[DpdHeadwordDbParts]] = list_into_batches(dpd_db_data, num_logical_cores)

        processes: List[Process] = []

        render_data = DpdHeadwordRenderData(
            pth = pth,
            word_templates = word_templates,
            sandhi_contractions = sandhi_contractions,
            cf_set = cf_set,
            idioms_set = idioms_set,
            make_link = make_link,
            show_id = show_id,
            show_ebt_count = show_ebt_count,
            show_sbs_data = show_sbs_data,
            show_ru_data = show_ru_data,
        )

        def _parse_batch(batch: List[DpdHeadwordDbParts]):
            res: List[Tuple[DictEntry, RenderedSizes]] = \
                [render_pali_word_dpd_html(i, render_data, lang, extended_synonyms, show_sbs_data) for i in batch]

            for i, j in res:
                dpd_data_results_list.append(i)
                rendered_sizes_results_list.append(j)

        for batch in batches:
            p = Process(target=_parse_batch, args=(batch,))

            p.start()
            processes.append(p)

        for p in processes:
            p.join()
        
        if offset % limit == 0:
            p_counter(offset, pali_words_count, batch[0]["pali_word"].lemma_1)

        offset += limit

    dpd_data_list = list(dpd_data_results_list)
    rendered_sizes = list(rendered_sizes_results_list)
    total_sizes = sum_rendered_sizes(rendered_sizes)
    
    return dpd_data_list, total_sizes


def render_dpd_definition_templ(
        __pth__: Union[ProjectPaths, RuPaths],
        i: DpdHeadword,
        dpd_definition_templ: Template,
        sbs: SBS|None,
        ru: Russian|None,
        make_link = False,
        show_id = False,
        show_ebt_count = False,
        show_sbs_data = False,
        lang="en"
) -> str:
    """render the definition of a word's most relevant information:
    1. pos
    2. case
    3 meaning
    4. summary
    5. degree of completion"""

    # pos
    if lang == "en":
        pos: str = i.pos
    elif lang == "ru":
        pos: str = ru_replace_abbreviations(i.pos)

    # plus_case
    plus_case: str = ""
    if i.plus_case is not None and i.plus_case:
        if lang == "en":
            plus_case: str = i.plus_case
        elif lang == "ru":
            plus_case: str = ru_replace_abbreviations(i.plus_case)
    
    # meaning
    if lang == "en":
        meaning = make_meaning_combo_html(i)
    elif lang == "ru":
        if ru:
            ru_meaning = make_ru_meaning_html(i, ru)
            if ru_meaning:
                meaning = ru_meaning
            else:
                meaning = make_meaning_combo_html(i)
        else:
            meaning = make_meaning_combo_html(i)
    
    summary = summarize_construction(i)
    complete = degree_of_completion(i)

    # id
    id: int = i.id

    # ebt_count
    ebt_count: int = i.ebt_count

    return str(
        dpd_definition_templ.render(
            i=i,
            sbs=sbs,
            make_link=make_link,
            pos=pos,
            plus_case=plus_case,
            meaning=meaning,
            summary=summary,
            complete=complete,
            id=id,
            show_id=show_id,
            show_ebt_count=show_ebt_count,
            show_sbs_data=show_sbs_data,
            ebt_count=ebt_count,
            )
        )


def render_button_box_templ(
        __pth__: Union[ProjectPaths, RuPaths],
        i: DpdHeadword,
        sbs: SBS,
        cf_set: Set[str],
        idioms_set: Set[str],
        button_box_templ: Template,
        lang="en",
        show_sbs_data=False
) -> str:
    """render buttons for each section of the dictionary"""

    if lang == "en":
        button_html = (
            '<a class="button" '
            'href="#" '
            'data-target="{target}">{name}</a>')

    elif lang == "ru":
        button_html = (
            '<a class="button_ru" '
            'href="#" '
            'data-target="{target}">{name}</a>')

    # grammar_button
    if i.needs_grammar_button or show_sbs_data:
        if lang == "en":
            grammar_button = button_html.format(
                target=f"grammar_{i.lemma_1_}", name="grammar")
        elif lang == "ru":
            grammar_button = button_html.format(
                target=f"grammar_ru_{i.lemma_1_}", name="грамматика")
    else:
        grammar_button = ""

    # example_button
    if i.needs_example_button:
        if lang == "en":
            example_button = button_html.format(
                target=f"example_{i.lemma_1_}", name="example")
        elif lang == "ru":
            example_button = button_html.format(
                target=f"example_ru_{i.lemma_1_}", name="пример")
    else:
        example_button = ""

    # examples_button
    if i.needs_examples_button:
        if lang == "en":
            examples_button = button_html.format(
                target=f"examples_{i.lemma_1_}", name="examples")
        elif lang == "ru":
            examples_button = button_html.format(
                target=f"examples_ru_{i.lemma_1_}", name="примеры")
    else:
        examples_button = ""

    # sbs_example_button
    sbs_example_button = ""
    if (
        show_sbs_data and
        sbs and
        (sbs.needs_sbs_example_button or sbs.needs_sbs_examples_button)
    ):
        sbs_example_button = button_html.format(
            target=f"sbs_example_{i.lemma_1_}", name="SBS")

    # conjugation_button
    if i.needs_conjugation_button:
        if lang == "en":
            conjugation_button = button_html.format(
                target=f"conjugation_{i.lemma_1_}", name="conjugation")
        elif lang == "ru":
            conjugation_button = button_html.format(
                target=f"conjugation_ru_{i.lemma_1_}", name="спряжения")
    else:
        conjugation_button = ""

    # declension_button
    if i.needs_declension_button:
        if lang == "en":
            declension_button = button_html.format(
                target=f"declension_{i.lemma_1_}", name="declension")
        elif lang == "ru":
            declension_button = button_html.format(
                target=f"declension_ru_{i.lemma_1_}", name="склонения")
    else:
        declension_button = ""

    # root_family_button
    if i.needs_root_family_button:
        if lang == "en":
            root_family_button = button_html.format(
                target=f"family_root_{i.lemma_1_}", name="root family")
        elif lang == "ru":
            root_family_button = button_html.format(
                target=f"family_root_ru_{i.lemma_1_}", name="семья корня")
    else:
        root_family_button = ""

    # word_family_button
    if i.needs_word_family_button:
        if lang == "en":
            word_family_button = button_html.format(
                target=f"family_word_{i.lemma_1_}", name="word family")
        elif lang == "ru":
            word_family_button = button_html.format(
                target=f"family_word_ru_{i.lemma_1_}", name="семья слова")
    else:
        word_family_button = ""

    # compound_family_button
    if i.needs_compound_family_button:
        if lang == "en":
            compound_family_button = button_html.format(
                target=f"family_compound_{i.lemma_1_}", name="compound family")
        elif lang == "ru":
            compound_family_button = button_html.format(
                target=f"family_compound_ru_{i.lemma_1_}", name="семья составного")

    elif i.needs_compound_families_button:
        if lang == "en":
            compound_family_button = button_html.format(
                target=f"family_compound_{i.lemma_1_}", name="compound families")
        elif lang == "ru":
            compound_family_button = button_html.format(
                target=f"family_compound_ru_{i.lemma_1_}", name="семья составных")
    else:
        compound_family_button = ""

    # idioms button
    if i.needs_idioms_button:
        if lang == "en":
            idioms_button = button_html.format(
                target=f"family_idiom_{i.lemma_1_}", name="idioms")
        elif lang == "ru":
            idioms_button = button_html.format(
                target=f"family_idiom_ru_{i.lemma_1_}", name="идиомы")
    else:
        idioms_button = ""

    # set_family_button
    if i.needs_set_button:
        if lang == "en":
            set_family_button = button_html.format(
                target=f"family_set_{i.lemma_1_}", name="set")
        elif lang == "ru":
            set_family_button = button_html.format(
                target=f"family_set_ru_{i.lemma_1_}", name="группа")

    elif i.needs_sets_button:
        if lang == "en":
            set_family_button = button_html.format(
                target=f"family_set_{i.lemma_1_}", name="sets")
        elif lang == "ru":
            set_family_button = button_html.format(
                target=f"family_set_ru_{i.lemma_1_}", name="группы")
    else:
        set_family_button = ""

    # frequency_button
    if i.needs_frequency_button:
        if lang == "en":
            frequency_button = button_html.format(
                target=f"frequency_{i.lemma_1_}", name="frequency")
        elif lang == "ru":
            frequency_button = button_html.format(
                target=f"frequency_ru_{i.lemma_1_}", name="частота")
    else:
        frequency_button = ""

    # feedback_button
    if lang == "en":
        feedback_button = button_html.format(
            target=f"feedback_{i.lemma_1_}", name="feedback")
    elif lang == "ru":
        feedback_button = button_html.format(
            target=f"feedback_ru_{i.lemma_1_}", name="о словаре")

    return str(
        button_box_templ.render(
            grammar_button=grammar_button,
            example_button=example_button,
            examples_button=examples_button,
            sbs_example_button=sbs_example_button,
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
        __pth__: Union[ProjectPaths, RuPaths],
        i: DpdHeadword,
        rt: DpdRoot,
        sbs: SBS,
        ru: Russian,
        grammar_templ: Template,
        lang="en",
        show_sbs_data=False,
        show_ru_data=False,
) -> str:
    """html table of grammatical information"""

    if (i.meaning_1 is not None and i.meaning_1) or show_sbs_data:
        if i.construction is not None and i.construction:
            i.construction = i.construction.replace("\n", "<br>")
        else:
            i.construction = ""

    if lang == "en":
        grammar = make_grammar_line(i)
    elif lang == "ru":
        grammar = ru_make_grammar_line(i)
    meaning = f"{make_meaning_combo_html(i)}"

    ru_base = ""
    if lang == "ru":
        ru_base = ru_replace_abbreviations(i.root_base, "base")

    ru_phonetic = ""
    if lang == "ru":
        ru_phonetic = ru_replace_abbreviations(i.phonetic, "phonetic")

    return str(
        grammar_templ.render(
            i=i,
            rt=rt,
            sbs=sbs,
            ru=ru,
            show_sbs_data=show_sbs_data,
            show_ru_data=show_ru_data,
            grammar=grammar,
            meaning=meaning,
            ru_base=ru_base,
            ru_phonetic=ru_phonetic,
            today=TODAY))


def render_example_templ(
        __pth__: Union[ProjectPaths, RuPaths],
        i: DpdHeadword,
        example_templ: Template,
        make_link=False
) -> str:
    """render sutta examples html"""

    return str(
        example_templ.render(
            i=i,
            make_link=make_link,
            today=TODAY))


def render_sbs_example_templ(
        __pth__: Union[ProjectPaths, RuPaths],
        i: DpdHeadword,
        sbs: SBS,
        sbs_example_templ: Template,
        make_link=False
) -> str:
    """render sbs examples html"""

    if any(getattr(sbs, f'sbs_example_{n}') for n in range(1, 5)):
        return str(
            sbs_example_templ.render(
                i=i,
                sbs=sbs,
                make_link=make_link))
    else:
        return ""


def render_inflection_templ(
        __pth__: Union[ProjectPaths, RuPaths],
        i: DpdHeadword,
        inflection_templ:Template,
        lang="en"
) -> str:
    """inflection or conjugation table"""

    if lang == "en":
        table=i.inflections_html
    elif lang == "ru":
        table: str = ru_replace_abbreviations(i.inflections_html, "inflect")

    return str(
        inflection_templ.render(
            i=i,
            table=table,
            today=TODAY,
            declensions=DECLENSIONS,
            conjugations=CONJUGATIONS))


def render_family_root_templ(
        __pth__: Union[ProjectPaths, RuPaths],
        i: DpdHeadword,
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
        __pth__: Union[ProjectPaths, RuPaths],
        i: DpdHeadword,
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
        __pth__: Union[ProjectPaths, RuPaths],
        i: DpdHeadword,
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
        __pth__: Union[ProjectPaths, RuPaths],
        i: DpdHeadword,
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
        __pth__: Union[ProjectPaths, RuPaths],
        i: DpdHeadword,
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
        __pth__: Union[ProjectPaths, RuPaths],
        i: DpdHeadword,
        frequency_templ: Template,
        lang="en"
) -> str:   
    """render html template of frequency table"""

    # make header
    if (
        i.freq_data_unpack["CstFreq"] == []
        and i.freq_data_unpack["BjtFreq"] == []
        and i.freq_data_unpack["SyaFreq"] == []
        and i.freq_data_unpack["ScFreq"] == []
    ):
        header = f"There are no matches of <b>{i.lemma_1}</b> in any corpus."
    
    else:
        if i.pos in INDECLINABLES or i.stem.startswith("!"):
            header = f"Frequency of <b>{i.lemma_1}</b>."
        elif i.pos in CONJUGATIONS:
            header = f"Frequency of <b>{i.lemma_1}</b> and its conjugations."
        elif i.pos in DECLENSIONS:
            header = f"Frequency of <b>{i.lemma_1}</b> and its declensions."

    if lang == "ru":
        header = replace_english(header)

    return str(
        frequency_templ.render(
            i=i,
            header=header,
            today=TODAY))


def render_feedback_templ(
        __pth__: Union[ProjectPaths, RuPaths],
        i: DpdHeadword,
        feedback_templ: Template
) -> str:
    """render html of feedback template"""

    return str(
        feedback_templ.render(
            i=i,
            today=TODAY))
