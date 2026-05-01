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
from exporter.deconstructor.data_classes import DeconstructorData


class GlobalVars:
    """Global variables."""

    def __init__(self) -> None:
        # config options
        if config_test("dictionary", "make_mdict", "yes"):
            self.make_mdict: bool = True
        elif config_test("dictionary", "make_mdict", "no"):
            self.make_mdict: bool = False

        self.make_slob = config_read("goldendict", "make_slob", "no") == "yes"

        # paths
        self.pth = ProjectPaths()

        # dict_data
        self.dict_data: list[DictEntry]


def make_deconstructor_dict_data(g: GlobalVars) -> None:
    """Prepare data set for GoldenDict of deconstructions and synonyms."""

    pr.green_tmr("making deconstructor data list")

    db_session = get_db_session(g.pth.dpd_db_path)
    deconstructor_db = db_session.query(Lookup).filter(Lookup.deconstructor != "").all()
    deconstructor_db_length: int = len(deconstructor_db)

    speech_marks_manager = SpeechMarkManager()
    speech_marks: SpeechMarksDict = speech_marks_manager.get_speech_marks()

    dict_data: list = []

    jinja_env = get_jinja2_env("exporter/deconstructor")
    template = jinja_env.get_template("deconstructor.jinja")

    pr.yes(len(deconstructor_db))

    for counter, i in enumerate(deconstructor_db):
        # Use ViewModel
        data = DeconstructorData(i, g.pth, jinja_env)
        html_string = data.header + minify(template.render(data=data))

        # make synonyms list
        synonyms = add_niggahitas([i.lookup_key], all=False)
        synonyms.extend(i.sinhala_unpack)
        synonyms.extend(i.devanagari_unpack)
        synonyms.extend(i.thai_unpack)
        if i.lookup_key in speech_marks:
            contractions = speech_marks.get(i.lookup_key, [])
            synonyms.extend(contractions)

        dict_data += [
            DictEntry(
                word=i.lookup_key,
                definition_html=html_string,
                definition_plain="",
                synonyms=synonyms,
            )
        ]

        if counter % 50000 == 0:
            pr.counter(counter, deconstructor_db_length, i.lookup_key)

    g.dict_data = dict_data
    db_session.close()


def prepare_and_export_to_gd_mdict(g: GlobalVars) -> None:
    """Prepare data to export to GoldenDict using pyglossary."""

    dict_info1 = DictInfo(
        bookname="DPD Deconstructor",
        author="Bodhirasa",
        description="<h3>DPD Deconstructor by Bodhirasa</h3><p>Automated compound deconstruction and sandhi-splitting of all words in <b>Chaṭṭha Saṅgāyana Tipitaka</b> and <b>Sutta Central</b> texts.</p><p>For more information please visit the <a href='https://digitalpalidictionary.github.io/features/deconstructor/'>Deconstrutor page</a> on the <a href='https://digitalpalidictionary.github.io'>DPD website</a>.</p>",
        website="https://digitalpalidictionary.github.io/features/deconstructor/",
        source_lang="pi",
        target_lang="pi",
    )

    dict_vars1 = DictVariables(
        css_paths=[g.pth.dpd_css_and_fonts_path],
        js_paths=None,
        gd_path=g.pth.share_dir,
        md_path=g.pth.share_dir,
        dict_name="dpd-deconstructor",
        icon_path=g.pth.dpd_logo_svg,
        font_path=g.pth.fonts_dir,
        zip_up=False,
        delete_original=False,
    )

    # the deconstructor is too large for goldendict, so needs to be split in two.
    # find the halfway mark to use as a split point
    half = int(len(g.dict_data) / 2)

    # export the first half of goldendict
    export_to_goldendict_with_pyglossary(
        dict_info1, dict_vars1, g.dict_data[:half], include_slob=g.make_slob
    )

    # export the other half of goldendict
    dict_info2 = DictInfo(
        bookname="DPD Deconstructor2",
        author="Bodhirasa",
        description="<h3>DPD Deconstructor by Bodhirasa</h3><p>Automated compound deconstruction and sandhi-splitting of all words in <b>Chaṭṭha Saṅgāyana Tipitaka</b> and <b>Sutta Central</b> texts.</p><p>For more information please visit the <a href='https://digitalpalidictionary.github.io/features/deconstructor/'>Deconstrutor page</a> on the <a href='https://digitalpalidictionary.github.io'>DPD website</a>.</p>",
        website="https://digitalpalidictionary.github.io/features/deconstructor/",
        source_lang="pi",
        target_lang="pi",
    )

    dict_vars2 = DictVariables(
        css_paths=[g.pth.dpd_css_and_fonts_path],
        js_paths=None,
        gd_path=g.pth.share_dir,
        md_path=g.pth.share_dir,
        dict_name="dpd-deconstructor2",
        icon_path=g.pth.dpd_logo_svg,
        font_path=g.pth.fonts_dir,
        zip_up=False,
        delete_original=False,
    )

    export_to_goldendict_with_pyglossary(
        dict_info2, dict_vars2, g.dict_data[half:], include_slob=g.make_slob
    )

    # export to mdict
    if g.make_mdict:
        export_to_mdict(dict_info1, dict_vars1, g.dict_data)


def main():
    pr.tic()
    pr.yellow_title("dpd deconstructor")

    # should the program run?
    if not config_test("exporter", "make_deconstructor", "yes"):
        pr.green_tmr("disabled in config.ini")
        return

    g = GlobalVars()
    make_deconstructor_dict_data(g)
    prepare_and_export_to_gd_mdict(g)
    pr.toc()


if __name__ == "__main__":
    main()
