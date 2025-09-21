"""Compile HTML data for DpdHeadword."""

from multiprocessing import Manager, Process
from multiprocessing.managers import ListProxy
from typing import List, Set, Tuple, TypedDict

import psutil

# from css_html_js_minify import css_minify, js_minify
from mako.template import Template
from minify_html import minify
from sqlalchemy.orm.session import Session
from sqlalchemy.sql import func

from db.models import (
    DpdHeadword,
    DpdRoot,
    FamilyCompound,
    FamilyIdiom,
    FamilyRoot,
    FamilySet,
    FamilyWord,
)
from exporter.goldendict.helpers import TODAY
from tools.configger import config_test
from tools.css_manager import CSSManager
from tools.date_and_time import year_month_day_dash
from tools.degree_of_completion import degree_of_completion
from tools.exporter_functions import (
    get_family_compounds,
    get_family_idioms,
    get_family_set,
)
from tools.goldendict_exporter import DictEntry
from tools.meaning_construction import make_grammar_line, make_meaning_combo_html
from tools.niggahitas import add_niggahitas
from tools.paths import ProjectPaths
from tools.pos import CONJUGATIONS, DECLENSIONS, INDECLINABLES
from tools.printer import printer as pr
from tools.sandhi_contraction import SandhiContractionDict
from tools.superscripter import superscripter_uni
from tools.utils import (
    RenderedSizes,
    default_rendered_sizes,
    list_into_batches,
    squash_whitespaces,
    sum_rendered_sizes,
)


class DpdHeadwordTemplates:
    def __init__(self, paths: ProjectPaths):
        self.paths = paths
        self.header_templ = Template(filename=str(paths.dpd_header_templ_path))
        self.dpd_definition_templ = Template(
            filename=str(paths.dpd_definition_templ_path)
        )
        self.button_box_templ = Template(filename=str(paths.button_box_templ_path))
        self.grammar_templ = Template(filename=str(paths.grammar_templ_path))
        self.example_templ = Template(filename=str(paths.example_templ_path))
        self.inflection_templ = Template(filename=str(paths.inflection_templ_path))
        self.family_root_templ = Template(filename=str(paths.family_root_templ_path))
        self.family_word_templ = Template(filename=str(paths.family_word_templ_path))
        self.family_compound_templ = Template(
            filename=str(paths.family_compound_templ_path)
        )
        self.family_idiom_templ = Template(filename=str(paths.family_idiom_templ_path))
        self.family_set_templ = Template(filename=str(paths.family_set_templ_path))
        self.frequency_templ = Template(filename=str(paths.frequency_templ_path))
        self.feedback_templ = Template(filename=str(paths.feedback_templ_path))

        self.dpd_css = ""
        self.button_js = ""


DpdHeadwordDbRowItems = Tuple[DpdHeadword, FamilyRoot, FamilyWord]


class DpdHeadwordDbParts(TypedDict):
    pali_word: DpdHeadword
    pali_root: DpdRoot
    family_root: FamilyRoot
    family_word: FamilyWord
    family_compounds: List[FamilyCompound]
    family_idioms: List[FamilyIdiom]
    family_set: List[FamilySet]


class DpdHeadwordRenderData(TypedDict):
    pth: ProjectPaths
    word_templates: DpdHeadwordTemplates
    sandhi_contractions: SandhiContractionDict
    cf_set: Set[str]
    idioms_set: Set[str]
    make_link: bool
    show_id: bool


def render_pali_word_dpd_html(
    db_parts: DpdHeadwordDbParts,
    render_data: DpdHeadwordRenderData,
) -> Tuple[DictEntry, RenderedSizes]:
    rd = render_data
    size_dict = default_rendered_sizes()

    i: DpdHeadword = db_parts["pali_word"]
    rt: DpdRoot = db_parts["pali_root"]
    fr: FamilyRoot = db_parts["family_root"]
    fw: FamilyWord = db_parts["family_word"]
    fc: List[FamilyCompound] = db_parts["family_compounds"]
    fi: List[FamilyIdiom] = db_parts["family_idioms"]
    fs: List[FamilySet] = db_parts["family_set"]
    date: str = year_month_day_dash()

    tt = rd["word_templates"]
    pth = rd["pth"]
    sandhi_contractions = rd["sandhi_contractions"]

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

    html: str = ""
    html += "<body>"

    summary = render_dpd_definition_templ(
        pth,
        i,
        tt.dpd_definition_templ,
        rd["make_link"],
        rd["show_id"],
    )
    html += summary
    size_dict["dpd_summary"] += len(summary)

    button_box = render_button_box_templ(
        pth,
        i,
        rd["cf_set"],
        rd["idioms_set"],
        tt.button_box_templ,
    )
    html += button_box
    size_dict["dpd_button_box"] += len(button_box)

    if i.needs_grammar_button:
        grammar = render_grammar_templ(
            pth,
            i,
            rt,
            tt.grammar_templ,
        )
        html += grammar
        size_dict["dpd_grammar"] += len(grammar)

    if i.needs_example_button or i.needs_examples_button:
        example = render_example_templ(pth, i, tt.example_templ, rd["make_link"])
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
            pth, i, fc, rd["cf_set"], tt.family_compound_templ
        )
        html += family_compound
        size_dict["dpd_family_compound"] += len(family_compound)

    if i.needs_idioms_button:
        family_idiom = render_family_idioms_templ(
            pth, i, fi, rd["idioms_set"], tt.family_idiom_templ
        )
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

    # Add CSS Variables and fonts to header
    header = str(tt.header_templ.render(i=i, date=date))
    css_manager = CSSManager()
    header = css_manager.update_style(header, "dpd")

    size_dict["dpd_header"] += len(header)
    html = squash_whitespaces(header) + minify(html)

    synonyms: List[str] = i.inflections_list_all  # include api ca eva iti
    synonyms = add_niggahitas(synonyms)
    for synonym in synonyms:
        if synonym in sandhi_contractions:
            contractions = sandhi_contractions[synonym]
            for contraction in contractions:
                if "'" in contraction:
                    synonyms.append(contraction)
    synonyms += i.inflections_sinhala_list
    synonyms += i.inflections_devanagari_list
    synonyms += i.inflections_thai_list
    synonyms += i.family_set_list
    synonyms += [str(i.id)]

    size_dict["dpd_synonyms"] += len(str(synonyms))

    res = DictEntry(
        word=i.lemma_1,
        definition_html=html,
        definition_plain="",
        synonyms=synonyms,
    )

    return (res, size_dict)


def generate_dpd_html(
    db_session: Session,
    pth: ProjectPaths,
    sandhi_contractions: SandhiContractionDict,
    cf_set: Set[str],
    idioms_set: set[str],
    make_link=False,
    data_limit: int = 0,
) -> Tuple[List[DictEntry], RenderedSizes]:
    pr.green_title("generating dpd html")

    paths = pth

    word_templates = DpdHeadwordTemplates(paths)

    if config_test("dictionary", "show_id", "yes"):
        show_id: bool = True
    else:
        show_id: bool = False

    dpd_data_list: List[DictEntry] = []

    pali_words_count = db_session.query(func.count(DpdHeadword.id)).scalar()

    # limit the data size for testing purposes
    if data_limit != 0:
        pali_words_count = data_limit

    # If the work items per loop are too high, low-memory systems will slow down
    # when multi-threading.
    #
    # Setting the threshold to 9 GB to make sure 8 GB systems are covered.
    low_mem_threshold = 9 * 1024 * 1024 * 1024
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
    pr.green_title(f"running with {num_logical_cores} cores")

    while offset <= pali_words_count:
        dpd_db_query = (
            db_session.query(DpdHeadword, FamilyRoot, FamilyWord)
            .outerjoin(
                FamilyRoot, DpdHeadword.root_family_key == FamilyRoot.root_family_key
            )
            .outerjoin(FamilyWord, DpdHeadword.family_word == FamilyWord.word_family)
            .order_by(DpdHeadword.lemma_1)
        )

        dpd_db = dpd_db_query.limit(limit).offset(offset).all()

        def _add_parts(i: DpdHeadwordDbRowItems) -> DpdHeadwordDbParts:
            pw: DpdHeadword
            fr: FamilyRoot
            fw: FamilyWord
            (
                pw,
                fr,
                fw,
            ) = i

            return DpdHeadwordDbParts(
                pali_word=pw,
                pali_root=pw.rt,
                family_root=fr,
                family_word=fw,
                family_compounds=get_family_compounds(pw),
                family_idioms=get_family_idioms(pw),
                family_set=get_family_set(pw),
            )

        dpd_db_data = [_add_parts(i.tuple()) for i in dpd_db]

        rendered_sizes: List[RenderedSizes] = []

        batches: List[List[DpdHeadwordDbParts]] = list_into_batches(
            dpd_db_data, num_logical_cores
        )

        processes: List[Process] = []

        render_data = DpdHeadwordRenderData(
            pth=pth,
            word_templates=word_templates,
            sandhi_contractions=sandhi_contractions,
            cf_set=cf_set,
            idioms_set=idioms_set,
            make_link=make_link,
            show_id=show_id,
        )

        def _parse_batch(batch: List[DpdHeadwordDbParts]):
            res: List[Tuple[DictEntry, RenderedSizes]] = [
                render_pali_word_dpd_html(i, render_data) for i in batch
            ]

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
            pr.counter(offset, pali_words_count, batch[0]["pali_word"].lemma_1)

        offset += limit

    dpd_data_list = list(dpd_data_results_list)
    rendered_sizes = list(rendered_sizes_results_list)
    total_sizes = sum_rendered_sizes(rendered_sizes)

    return dpd_data_list, total_sizes


def render_dpd_definition_templ(
    __pth__: ProjectPaths,
    i: DpdHeadword,
    dpd_definition_templ: Template,
    make_link=False,
    show_id=False,
) -> str:
    """render the definition of a word's most relevant information:
    1. pos
    2. case
    3 meaning
    4. summary
    5. degree of completion"""

    pos: str = i.pos

    # plus_case
    plus_case: str = ""
    if i.plus_case is not None and i.plus_case:
        plus_case: str = i.plus_case

    # meaning
    meaning = make_meaning_combo_html(i)
    summary = i.construction_summary
    complete = degree_of_completion(i)

    # id
    id: int = i.id

    return str(
        dpd_definition_templ.render(
            i=i,
            make_link=make_link,
            pos=pos,
            plus_case=plus_case,
            meaning=meaning,
            summary=summary,
            complete=complete,
            id=id,
            show_id=show_id,
        )
    )


def render_button_box_templ(
    __pth__: ProjectPaths,
    i: DpdHeadword,
    cf_set: Set[str],
    idioms_set: Set[str],
    button_box_templ: Template,
) -> str:
    """render buttons for each section of the dictionary"""

    button_html = '<a class="button" href="#" data-target="{target}">{name}</a>'

    # grammar_button
    if i.needs_grammar_button:
        grammar_button = button_html.format(
            target=f"grammar_{i.lemma_1_}", name="grammar"
        )
    else:
        grammar_button = ""

    # example_button
    if i.needs_example_button:
        example_button = button_html.format(
            target=f"example_{i.lemma_1_}", name="example"
        )
    else:
        example_button = ""

    # examples_button
    if i.needs_examples_button:
        examples_button = button_html.format(
            target=f"examples_{i.lemma_1_}", name="examples"
        )
    else:
        examples_button = ""

    # conjugation_button
    if i.needs_conjugation_button:
        conjugation_button = button_html.format(
            target=f"conjugation_{i.lemma_1_}", name="conjugation"
        )
    else:
        conjugation_button = ""

    # declension_button
    if i.needs_declension_button:
        declension_button = button_html.format(
            target=f"declension_{i.lemma_1_}", name="declension"
        )
    else:
        declension_button = ""

    # root_family_button
    if i.needs_root_family_button:
        root_family_button = button_html.format(
            target=f"family_root_{i.lemma_1_}", name="root family"
        )
    else:
        root_family_button = ""

    # word_family_button
    if i.needs_word_family_button:
        word_family_button = button_html.format(
            target=f"family_word_{i.lemma_1_}", name="word family"
        )
    else:
        word_family_button = ""

    # compound_family_button
    if i.needs_compound_family_button:
        compound_family_button = button_html.format(
            target=f"family_compound_{i.lemma_1_}", name="compound family"
        )

    elif i.needs_compound_families_button:
        compound_family_button = button_html.format(
            target=f"family_compound_{i.lemma_1_}", name="compound families"
        )
    else:
        compound_family_button = ""

    # idioms button
    if i.needs_idioms_button:
        idioms_button = button_html.format(
            target=f"family_idiom_{i.lemma_1_}", name="idioms"
        )
    else:
        idioms_button = ""

    # set_family_button
    if i.needs_set_button:
        set_family_button = button_html.format(
            target=f"family_set_{i.lemma_1_}", name="set"
        )

    elif i.needs_sets_button:
        set_family_button = button_html.format(
            target=f"family_set_{i.lemma_1_}", name="sets"
        )
    else:
        set_family_button = ""

    # frequency_button
    if i.needs_frequency_button:
        frequency_button = button_html.format(
            target=f"frequency_{i.lemma_1_}", name="frequency"
        )
    else:
        frequency_button = ""

    # feedback_button
    feedback_button = button_html.format(
        target=f"feedback_{i.lemma_1_}", name="feedback"
    )

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
            feedback_button=feedback_button,
        )
    )


def render_grammar_templ(
    __pth__: ProjectPaths,
    i: DpdHeadword,
    rt: DpdRoot,
    grammar_templ: Template,
) -> str:
    """html table of grammatical information"""

    if i.meaning_1 is not None and i.meaning_1:
        if i.construction is not None and i.construction:
            i.construction = i.construction.replace("\n", "<br>")
        else:
            i.construction = ""

    grammar = make_grammar_line(i)
    meaning = f"{make_meaning_combo_html(i)}"

    return str(
        grammar_templ.render(
            i=i,
            rt=rt,
            grammar=grammar,
            meaning=meaning,
            today=TODAY,
        )
    )


def render_example_templ(
    __pth__: ProjectPaths,
    i: DpdHeadword,
    example_templ: Template,
    make_link=False,
) -> str:
    """render sutta examples html"""

    return str(example_templ.render(i=i, make_link=make_link, today=TODAY))


def render_inflection_templ(
    __pth__: ProjectPaths,
    i: DpdHeadword,
    inflection_templ: Template,
) -> str:
    """inflection or conjugation table"""

    table = i.inflections_html

    return str(
        inflection_templ.render(
            i=i,
            table=table,
            today=TODAY,
            declensions=DECLENSIONS,
            conjugations=CONJUGATIONS,
        )
    )


def render_family_root_templ(
    __pth__: ProjectPaths,
    i: DpdHeadword,
    fr: FamilyRoot,
    family_root_templ,
) -> str:
    """render html table of all words with the same prefix and root"""

    return str(family_root_templ.render(i=i, fr=fr, today=TODAY))


def render_family_word_templ(
    __pth__: ProjectPaths,
    i: DpdHeadword,
    fw: FamilyWord,
    family_word_templ: Template,
) -> str:
    """render html of all words which belong to the same family"""

    return str(family_word_templ.render(i=i, fw=fw, today=TODAY))


def render_family_compound_templ(
    __pth__: ProjectPaths,
    i: DpdHeadword,
    fc: List[FamilyCompound],
    cf_set: Set[str],
    family_compound_templ: Template,
) -> str:
    """render html table of all words containing the same compound"""

    return str(
        family_compound_templ.render(
            i=i, fc=fc, superscripter_uni=superscripter_uni, today=TODAY
        )
    )


def render_family_idioms_templ(
    __pth__: ProjectPaths,
    i: DpdHeadword,
    fi: List[FamilyIdiom],
    idioms_set: Set[str],
    family_idioms_template: Template,
) -> str:
    """render html table of all words containing the same compound"""

    return str(
        family_idioms_template.render(
            i=i, fi=fi, superscripter_uni=superscripter_uni, today=TODAY
        )
    )


def render_family_set_templ(
    __pth__: ProjectPaths,
    i: DpdHeadword,
    fs: List[FamilySet],
    family_set_templ: Template,
) -> str:
    """render html table of all words belonging to the same set"""

    return str(
        family_set_templ.render(
            i=i, fs=fs, superscripter_uni=superscripter_uni, today=TODAY
        )
    )


def render_frequency_templ(
    __pth__: ProjectPaths,
    i: DpdHeadword,
    frequency_templ: Template,
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

    return str(frequency_templ.render(i=i, header=header, today=TODAY))


def render_feedback_templ(
    __pth__: ProjectPaths,
    i: DpdHeadword,
    feedback_templ: Template,
) -> str:
    """render html of feedback template"""

    return str(feedback_templ.render(i=i, today=TODAY))
