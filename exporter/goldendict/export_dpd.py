"""Compile HTML data for DpdHeadword."""

from multiprocessing import Manager, Process
from multiprocessing.managers import ListProxy
from typing import List, Set, Tuple, TypedDict

import psutil

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
    SuttaInfo,
)
from tools.configger import config_test
from tools.exporter_functions import (
    get_family_compounds,
    get_family_idioms,
    get_family_set,
)
from tools.goldendict_exporter import DictEntry
from tools.niggahitas import add_niggahitas
from tools.paths import ProjectPaths
from tools.printer import printer as pr
from tools.speech_marks import SpeechMarksDict
from tools.utils import (
    RenderedSizes,
    default_rendered_sizes,
    list_into_batches,
    squash_whitespaces,
    sum_rendered_sizes,
)
from exporter.jinja2_env import get_jinja2_env
from exporter.goldendict.data_classes import HeadwordData


DpdHeadwordDbRowItems = Tuple[DpdHeadword, FamilyRoot, FamilyWord]


class DpdHeadwordDbParts(TypedDict):
    pali_word: DpdHeadword
    pali_root: DpdRoot
    family_root: FamilyRoot
    family_word: FamilyWord
    family_compounds: List[FamilyCompound]
    family_idioms: List[FamilyIdiom]
    family_set: List[FamilySet]
    sutta_info: SuttaInfo


class DpdHeadwordRenderDataBase(TypedDict):
    speech_marks: SpeechMarksDict
    cf_set: Set[str]
    idioms_set: Set[str]
    show_id: bool


class DpdHeadwordRenderData(DpdHeadwordRenderDataBase):
    pth: ProjectPaths
    jinja_env: any


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
    su: SuttaInfo = db_parts["sutta_info"]

    pth = rd["pth"]
    jinja_env = rd["jinja_env"]
    speech_marks = rd["speech_marks"]

    # Use ViewModel
    data = HeadwordData(
        i=i,
        rt=rt,
        fr=fr,
        fw=fw,
        fc=fc,
        fi=fi,
        fs=fs,
        su=su,
        pth=pth,
        jinja_env=jinja_env,
        cf_set=rd["cf_set"],
        idioms_set=rd["idioms_set"],
        show_id=rd["show_id"]
    )
    
    template = jinja_env.get_template("dpd_headword.jinja")
    html = template.render(d=data)

    # Re-calculate parts for parity
    header = data.header
    body_start = html.find("<body>")
    body = html[body_start:]
    
    final_html = squash_whitespaces(header) + minify(body)
    
    size_dict["dpd_header"] += len(header)
    size_dict["dpd_summary"] += len(data.meaning_combo_html)

    # synonyms
    synonyms: List[str] = i.inflections_list_all
    synonyms = add_niggahitas(synonyms)

    for synonym in synonyms:
        if synonym in speech_marks:
            contractions = speech_marks[synonym]
            for contraction in contractions:
                if "'" in contraction:
                    synonyms.append(contraction)

    synonyms += i.inflections_sinhala_list
    synonyms += i.inflections_devanagari_list
    synonyms += i.inflections_thai_list
    synonyms += i.family_set_list
    synonyms += [str(i.id)]

    if i.needs_sutta_info_button:
        synonyms += i.su.sutta_codes_list

    size_dict["dpd_synonyms"] += len(str(synonyms))

    res = DictEntry(
        word=i.lemma_1,
        definition_html=final_html,
        definition_plain="",
        synonyms=synonyms,
    )

    return (res, size_dict)


def _parse_batch_top_level(
    batch: List[DpdHeadwordDbParts],
    path: ProjectPaths,
    render_data: DpdHeadwordRenderData,
    dpd_data_results_list: ListProxy,
    rendered_sizes_results_list: ListProxy,
):
    """Helper function for multiprocessing."""
    jinja_env = get_jinja2_env("exporter/goldendict/templates")

    full_render_data: DpdHeadwordRenderData = {
        **render_data,
        "pth": path,
        "jinja_env": jinja_env,
    }

    res: List[Tuple[DictEntry, RenderedSizes]] = [
        render_pali_word_dpd_html(
            i,
            full_render_data,
        )
        for i in batch
    ]

    for i, j in res:
        dpd_data_results_list.append(i)
        rendered_sizes_results_list.append(j)


def generate_dpd_html(
    db_session: Session,
    pth: ProjectPaths,
    speech_marks: SpeechMarksDict,
    cf_set: Set[str],
    idioms_set: set[str],
    data_limit: int = 0,
) -> Tuple[List[DictEntry], RenderedSizes]:
    pr.green_title("generating dpd html")

    if config_test("dictionary", "show_id", "yes"):
        show_id: bool = True
    else:
        show_id: bool = False

    pali_words_count = db_session.query(func.count(DpdHeadword.id)).scalar()

    if data_limit != 0:
        pali_words_count = data_limit

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
    if num_logical_cores is None:
        num_logical_cores = 1
    pr.green_title(f"running with {num_logical_cores} cores")

    while offset < pali_words_count:
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
            pw, fr, fw = i
            return {
                "pali_word": pw,
                "pali_root": pw.rt,
                "family_root": fr,
                "family_word": fw,
                "family_compounds": get_family_compounds(pw),
                "family_idioms": get_family_idioms(pw),
                "family_set": get_family_set(pw),
                "sutta_info": pw.su,
            }

        dpd_db_data = [_add_parts(i.tuple()) for i in dpd_db]

        batches: List[List[DpdHeadwordDbParts]] = list_into_batches(
            dpd_db_data, num_logical_cores
        )

        processes: List[Process] = []

        render_data: DpdHeadwordRenderDataBase = {
            "speech_marks": speech_marks,
            "cf_set": cf_set,
            "idioms_set": idioms_set,
            "show_id": show_id,
        }

        for batch in batches:
            p = Process(
                target=_parse_batch_top_level,
                args=(
                    batch,
                    pth,
                    render_data,
                    dpd_data_results_list,
                    rendered_sizes_results_list,
                ),
            )
            p.start()
            processes.append(p)

        for p in processes:
            p.join()

        if len(batches) > 0 and len(batches[0]) > 0 and offset % limit == 0:
            pr.counter(offset, pali_words_count, batches[0][0]["pali_word"].lemma_1)

        offset += limit

    dpd_data_list = list(dpd_data_results_list)
    rendered_sizes = list(rendered_sizes_results_list)
    total_sizes = sum_rendered_sizes(rendered_sizes)

    return dpd_data_list, total_sizes
