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

        # exporter/ebook/
        self.epub_dir = base_dir.joinpath(Path("exporter/ru_components/ebook/epub/"))
        self.kindlegen_path = base_dir.joinpath(Path("exporter/ebook/kindlegen"))

        # # exporter/ebook/epub
        self.epub_text_dir = base_dir.joinpath(Path("exporter/ru_components/ebook/epub/OEBPS/Text"))
        self.epub_content_opf_path = base_dir.joinpath(Path("exporter/ru_components/ebook/epub/OEBPS/content.opf"))
        self.epub_abbreviations_path = base_dir.joinpath(Path("exporter/ru_components/ebook/epub/OEBPS/Text/abbreviations.xhtml"))
        self.epub_titlepage_path = base_dir.joinpath(Path("exporter/ru_components/ebook/epub/OEBPS/Text/titlepage.xhtml"))

        # # exporter/ebook/templates
        self.ebook_letter_templ_path = base_dir.joinpath(Path("exporter/ru_components/templates/ebook_ru_letter.html"))
        self.ebook_grammar_templ_path = base_dir.joinpath(Path("exporter/ru_components/templates/ebook_ru_grammar.html"))
        self.ebook_example_templ_path = base_dir.joinpath(Path("exporter/ru_components/templates/ebook_ru_example.html"))
        self.ebook_abbrev_entry_templ_path = base_dir.joinpath(Path("exporter/ru_components/templates/ebook_ru_abbreviation_entry.html"))
        self.ebook_title_page_templ_path = base_dir.joinpath(Path("exporter/ru_components/templates/ebook_ru_titlepage.html"))
        self.ebook_content_opf_templ_path = base_dir.joinpath(Path("exporter/ru_components/templates/ebook_ru_content_opf.html"))

        # /exporter/ru_components/css/
        self.dpd_css_path = base_dir.joinpath(Path("exporter/ru_components/css/dpd_ru.css"))

        # /exporter/goldendict/javascript/
        self.buttons_js_path = base_dir.joinpath(Path("exporter/goldendict/javascript//buttons.js"))
        self.sorter_js_path = base_dir.joinpath(Path("exporter/goldendict/javascript//sorter.js"))

        # /exporter/share
        self.share_dir = base_dir.joinpath(Path("exporter/share"))
        self.dpd_output_dir = base_dir.joinpath(Path("exporter/share/ru-dpd.zip"))
        self.mdict_mdx_path = base_dir.joinpath(Path("exporter/share/ru-dpd-mdict.mdx"))
        self.grammar_dict_dir = base_dir.joinpath(Path("exporter/share/ru-dpd-grammar.zip"))
        self.grammar_dict_mdict_path = base_dir.joinpath(Path("exporter/share/ru-dpd-grammar-mdict.mdx"))
        self.deconstructor_output_dir = base_dir.joinpath(Path("exporter/share/ru-dpd-deconstructor.zip"))
        self.deconstructor_mdict_mdx_path = base_dir.joinpath(Path("exporter/share/ru-dpd-deconstructor-mdict.mdx"))
        self.dpd_goldendict_zip_path = base_dir.joinpath(Path("exporter/share/ru-dpd-goldendict.zip"))
        self.dpd_mdict_zip_path = base_dir.joinpath(Path("exporter/share/ru-dpd-mdict.zip"))
        self.dpd_mobi_path = base_dir.joinpath(Path("exporter/share/ru-dpd-kindle.mobi"))
        self.dpd_epub_path = base_dir.joinpath(Path("exporter/share/ru-dpd-kindle.epub"))

        # /exporter/ru_components/templates
        self.templates_dir = base_dir.joinpath(Path("exporter/ru_components/templates"))
        self.header_templ_path = base_dir.joinpath(Path("exporter/ru_components/templates/header_ru.html"))
        self.header_plain_templ_path = base_dir.joinpath(Path("exporter/ru_components/templates/header_plain_ru.html"))
        self.dpd_definition_templ_path = base_dir.joinpath(Path("exporter/ru_components/templates/dpd_ru_definition.html"))
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
        self.deconstructor_templ_path = base_dir.joinpath(Path("exporter/ru_components/templates/deconstructor_ru.html"))

        # /icon
        self.icon_bmp_path = base_dir.joinpath(Path("exporter/ru_components/icon/book.bmp"))
        self.icon_path = base_dir.joinpath(Path("exporter/ru_components/icon/book.bmp"))

        if create_dirs:
            self.create_dirs()


    def create_dirs(self):
            for d in [
                self.templates_dir,
                self.share_dir,
                self.epub_dir,
                self.epub_text_dir
            ]:
                d.mkdir(parents=True, exist_ok=True)

