#!/usr/bin/env python3

"""Export Deconstructor To GoldenDict and MDict formats."""

from db.db_helpers import get_db_session
from db.models import Lookup
from tools.configger import config_read, config_test
from tools.goldendict_exporter import (
    DictEntry,
    DictInfo,
    DictVariables,
    export_to_goldendict_with_pyglossary,
)
from tools.mdict_exporter import export_to_mdict
from tools.niggahitas import add_niggahitas
from tools.paths import ProjectPaths
from tools.printer import printer as pr
from tools.speech_marks import SpeechMarkManager, SpeechMarksDict
from minify_html import minify
from exporter.jinja2_env import get_jinja2_env
from exporter.deconstructor.data_classes import (
    DeconstructorData,
    generate_deconstructor_header,
)

DECONSTRUCTOR_DESCRIPTION = "<h3>DPD Deconstructor by Bodhirasa</h3><p>Automated compound deconstruction and sandhi-splitting of all words in <b>Chaṭṭha Saṅgāyana Tipitaka</b> and <b>Sutta Central</b> texts.</p><p>For more information please visit the <a href='https://digitalpalidictionary.github.io/features/deconstructor/'>Deconstructor page</a> on the <a href='https://digitalpalidictionary.github.io'>DPD website</a>.</p>"


class GlobalVars:
    """Global variables."""

    def __init__(self) -> None:
        # config options
        self.make_mdict: bool = config_test("dictionary", "make_mdict", "yes")
        self.make_slob = config_read("goldendict", "make_slob", "no") == "yes"

        # paths
        self.pth = ProjectPaths()

        # dict_data
        self.dict_data: list[DictEntry]


def _make_synonyms(i: Lookup, speech_marks: SpeechMarksDict) -> list[str]:
    """Assemble the synonyms list for a single deconstructor entry."""
    synonyms = add_niggahitas([i.lookup_key], all=False)
    synonyms.extend(i.sinhala_unpack)
    synonyms.extend(i.devanagari_unpack)
    synonyms.extend(i.thai_unpack)
    synonyms.extend(speech_marks.get(i.lookup_key, []))
    return synonyms


def _make_dict_info(bookname: str) -> DictInfo:
    return DictInfo(
        bookname=bookname,
        author="Bodhirasa",
        description=DECONSTRUCTOR_DESCRIPTION,
        website="https://digitalpalidictionary.github.io/features/deconstructor/",
        source_lang="pi",
        target_lang="pi",
    )


def _make_dict_vars(dict_name: str, pth: ProjectPaths) -> DictVariables:
    return DictVariables(
        css_paths=[pth.dpd_css_and_fonts_path],
        js_paths=None,
        gd_path=pth.share_dir,
        md_path=pth.share_dir,
        dict_name=dict_name,
        icon_path=pth.dpd_logo_svg,
        font_path=pth.fonts_dir,
        zip_up=False,
        delete_original=False,
    )


def make_deconstructor_dict_data(g: GlobalVars) -> None:
    """Prepare data set for GoldenDict of deconstructions and synonyms."""

    pr.green_tmr("making deconstructor data list")

    db_session = get_db_session(g.pth.dpd_db_path)
    deconstructor_db = db_session.query(Lookup).filter(Lookup.deconstructor != "").all()
    deconstructor_db_length: int = len(deconstructor_db)

    speech_marks_manager = SpeechMarkManager()
    speech_marks: SpeechMarksDict = speech_marks_manager.get_speech_marks()

    dict_data: list[DictEntry] = []

    jinja_env = get_jinja2_env("exporter/deconstructor")
    template = jinja_env.get_template("deconstructor.jinja")
    header = generate_deconstructor_header(jinja_env)

    pr.yes(deconstructor_db_length)

    for counter, i in enumerate(deconstructor_db):
        data = DeconstructorData(i)
        html_string = header + minify(template.render(data=data))

        dict_data.append(
            DictEntry(
                word=i.lookup_key,
                definition_html=html_string,
                definition_plain="",
                synonyms=_make_synonyms(i, speech_marks),
            )
        )

        if counter % 50000 == 0:
            pr.counter(counter, deconstructor_db_length, i.lookup_key)

    g.dict_data = dict_data
    db_session.close()


def prepare_and_export_to_gd_mdict(g: GlobalVars) -> None:
    """Prepare data to export to GoldenDict using pyglossary."""

    dict_info1 = _make_dict_info("DPD Deconstructor")
    dict_vars1 = _make_dict_vars("dpd-deconstructor", g.pth)

    # the deconstructor is too large for goldendict, so needs to be split in two.
    # find the halfway mark to use as a split point
    half = int(len(g.dict_data) / 2)

    export_to_goldendict_with_pyglossary(
        dict_info1, dict_vars1, g.dict_data[:half], include_slob=g.make_slob
    )

    dict_info2 = _make_dict_info("DPD Deconstructor2")
    dict_vars2 = _make_dict_vars("dpd-deconstructor2", g.pth)

    export_to_goldendict_with_pyglossary(
        dict_info2, dict_vars2, g.dict_data[half:], include_slob=g.make_slob
    )

    if g.make_mdict:
        export_to_mdict(dict_info1, dict_vars1, g.dict_data)


def main() -> None:
    pr.tic()
    pr.yellow_title("dpd deconstructor")

    if not config_test("exporter", "make_deconstructor", "yes"):
        pr.green_title("disabled in config.ini")
        pr.toc()
        return

    g = GlobalVars()
    make_deconstructor_dict_data(g)
    prepare_and_export_to_gd_mdict(g)
    pr.toc()


if __name__ == "__main__":
    main()
