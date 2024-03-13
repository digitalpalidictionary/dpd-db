"""All file paths that get used in the russian exporter related codes."""

import os
from typing import Optional
from pathlib import Path

class RuPaths:

    def __init__(self, base_dir: Optional[Path] = None, create_dirs = True):

        if base_dir is None:
            # The current working directory of the shell.
            base_dir = Path(os.path.abspath("."))

        # /exporter/ru_components/tsvs/
        self.sets_ru_path = base_dir.joinpath(Path("exporter/ru_components/tsvs/sets_ru.tsv"))

        # /exporter/ru_components/css/
        self.dpd_css_path = base_dir.joinpath(Path("exporter/ru_components/css/dpd_ru.css"))

        # /exporter/goldendict/javascript/
        self.buttons_js_path = base_dir.joinpath(Path("exporter/goldendict/javascript//buttons.js"))
        self.sorter_js_path = base_dir.joinpath(Path("exporter/goldendict/javascript//sorter.js"))

        # /exporter/share
        self.share_dir = base_dir.joinpath(Path("exporter/share"))
        self.dpd_zip_path = base_dir.joinpath(Path("exporter/share/ru-dpd.zip"))
        self.mdict_mdx_path = base_dir.joinpath(Path("exporter/share/ru-dpd-mdict.mdx"))

        # /exporter/ru_components/templates
        self.templates_dir = base_dir.joinpath(Path("exporter/ru_components/templates"))
        self.header_templ_path = base_dir.joinpath(Path("exporter/ru_components/templates/header_ru.html"))
        self.dpd_definition_templ_path = base_dir.joinpath(Path("exporter/ru_components/templates/dpd_ru_defintion.html"))
        self.button_box_templ_path = base_dir.joinpath(Path("exporter/ru_components/templates/dpd_ru_button_box.html"))
        self.grammar_templ_path = base_dir.joinpath(Path("exporter/ru_components/templates/dpd_ru_grammar.html"))
        self.example_templ_path = base_dir.joinpath(Path("exporter/ru_components/templates/dpd_ru_example.html"))
        self.sbs_example_templ_path = base_dir.joinpath(Path("exporter/goldendict/templates/sbs_example.html"))
        self.inflection_templ_path = base_dir.joinpath(Path("exporter/ru_components/templates/dpd_ru_inflection.html"))
        self.family_root_templ_path = base_dir.joinpath(Path("exporter/ru_components/templates/dpd_ru_family_root.html"))
        self.family_word_templ_path = base_dir.joinpath(Path("exporter/ru_components/templates/dpd_ru_family_word.html"))
        self.family_compound_templ_path = base_dir.joinpath(Path("exporter/ru_components/templates/dpd_ru_family_compound.html"))
        self.family_idiom_templ_path = base_dir.joinpath(Path("exporter/ru_components/templates/dpd_ru_family_idiom.html"))
        self.family_set_templ_path = base_dir.joinpath(Path("exporter/ru_components/templates/dpd_ru_family_set.html"))
        self.frequency_templ_path = base_dir.joinpath(Path("exporter/ru_components/templates/dpd_ru_frequency.html"))
        self.feedback_templ_path = base_dir.joinpath(Path("exporter/ru_components/templates/dpd_ru_feedback.html"))
        self.variant_templ_path = base_dir.joinpath(Path("exporter/ru_components/templates/dpd_ru_variant_reading.html"))
        self.spelling_templ_path = base_dir.joinpath(Path("exporter/ru_components/templates/dpd_ru_spelling_mistake.html"))
        
        # # root templates
        self.root_definition_templ_path = base_dir.joinpath(Path("exporter/ru_components/templates/root_definition_ru.html"))
        self.root_button_templ_path = base_dir.joinpath(Path("exporter/ru_components/templates/root_buttons_ru.html"))
        self.root_info_templ_path = base_dir.joinpath(Path("exporter/ru_components/templates/root_info_ru.html"))
        self.root_matrix_templ_path = base_dir.joinpath(Path("exporter/ru_components/templates/root_matrix_ru.html"))
        self.root_families_templ_path = base_dir.joinpath(Path("exporter/ru_components/templates/root_families_ru.html"))

        # # other templates
        self.epd_templ_path = base_dir.joinpath(Path("exporter/ru_components/templates/rpd.html"))
        self.abbrev_templ_path = base_dir.joinpath(Path("exporter/ru_components/templates/help_abbrev.html"))
        self.help_templ_path = base_dir.joinpath(Path("exporter/ru_components/templates/help_help.html"))

        # /icon
        self.icon_bmp_path = base_dir.joinpath(Path("exporter/ru_components/icon/book.bmp"))
        self.icon_path = base_dir.joinpath(Path("exporter/ru_components/icon/book.bmp"))

        if create_dirs:
            self.create_dirs()


    def create_dirs(self):
            for d in [
                self.templates_dir,
                self.share_dir
            ]:
                d.mkdir(parents=True, exist_ok=True)

