"""All file paths that get used in the russian exporter related codes."""

import os
from typing import Optional
from pathlib import Path

class RuPaths:

    def __init__(self, base_dir: Optional[Path] = None, create_dirs = True):

        if base_dir is None:
            # The current working directory of the shell.
            base_dir = Path(os.path.abspath("."))

        # /tsvs/
        self.sets_ru_path = base_dir / "exporter/goldendict/ru_components/tsvs/sets_ru.tsv"

        # /kindle/
        self.epub_dir = base_dir / "exporter/kindle/ru_components/kindle/epub/"
        self.kindlegen_path = base_dir / "exporter/kindle/kindlegen"

        # /kindle/epub
        self.epub_text_dir = base_dir / "exporter/kindle/ru_components/kindle/epub/OEBPS/Text"
        self.epub_content_opf_path = base_dir / "exporter/kindle/ru_components/kindle/epub/OEBPS/content.opf"
        self.epub_abbreviations_path = base_dir / "exporter/kindle/ru_components/kindle/epub/OEBPS/Text/abbreviations.xhtml"
        self.epub_titlepage_path = base_dir / "exporter/kindle/ru_components/kindle/epub/OEBPS/Text/titlepage.xhtml"

        # /kindle/templates
        self.ebook_letter_templ_path = base_dir / "exporter/kindle/ru_components/templates/ebook_ru_letter.html"
        self.ebook_grammar_templ_path = base_dir / "exporter/kindle/ru_components/templates/ebook_ru_grammar.html"
        self.ebook_example_templ_path = base_dir / "exporter/kindle/ru_components/templates/ebook_ru_example.html"
        self.ebook_abbrev_entry_templ_path = base_dir / "exporter/kindle/ru_components/templates/ebook_ru_abbreviation_entry.html"
        self.ebook_title_page_templ_path = base_dir / "exporter/kindle/ru_components/templates/ebook_ru_titlepage.html"
        self.ebook_content_opf_templ_path = base_dir / "exporter/kindle/ru_components/templates/ebook_ru_content_opf.html"

        # /goldendict/ru_components/css/
        self.dpd_css_path = base_dir / "exporter/goldendict/ru_components/css/dpd_ru.css"

        # /goldendict/ru_components/javascript/
        self.main_js_path = base_dir / "exporter/goldendict/ru_components/javascript/ru_main.js"
        self.buttons_js_path = base_dir / "exporter/goldendict/javascript/buttons.js"

        self.family_compound_json = base_dir / "exporter/goldendict/ru_components/javascript/ru_family_compound_json.js"
        self.family_idiom_json = base_dir / "exporter/goldendict/ru_components/javascript/ru_family_idiom_json.js"
        self.family_root_json = base_dir / "exporter/goldendict/ru_components/javascript/ru_family_root_json.js"
        self.family_set_json = base_dir / "exporter/goldendict/ru_components/javascript/ru_family_set_json.js"
        self.family_word_json = base_dir / "exporter/goldendict/ru_components/javascript/ru_family_word_json.js"

        self.family_compound_template_js = base_dir / "exporter/goldendict/ru_components/javascript/ru_family_compound_template.js"
        self.family_idiom_template_js = base_dir / "exporter/goldendict/ru_components/javascript/ru_family_idiom_template.js"
        self.family_root_template_js = base_dir / "exporter/goldendict/ru_components/javascript/ru_family_root_template.js"
        self.family_set_template_js = base_dir / "exporter/goldendict/ru_components/javascript/ru_family_set_template.js"
        self.family_word_template_js = base_dir / "exporter/goldendict/ru_components/javascript/ru_family_word_template.js"
        self.feedback_template_js = base_dir / "exporter/goldendict/ru_components/javascript/ru_feedback_template.js"

        # /share/goldendict
        self.share_dir = base_dir / "exporter/share"

        self.dpd_goldendict_dir = base_dir / "exporter/share/ru-dpd/"
        self.grammar_dict_goldendict_dir = base_dir / "exporter/share/ru-dpd-grammar/"
        self.deconstructor_goldendict_dir = base_dir / "exporter/share/ru-dpd-deconstructor/"
        
        self.dpd_mobi_path = base_dir / "exporter/share/ru-dpd-kindle.mobi"
        self.dpd_epub_path = base_dir / "exporter/share/ru-dpd-kindle.epub"

        self.dpd_goldendict_zip_path = base_dir / "exporter/share/ru-dpd-goldendict.zip"
        self.dpd_mdict_zip_path = base_dir / "exporter/share/ru-dpd-mdict.zip"

        # /share/mdict
        self.mdict_mdx_path = base_dir / "exporter/share/ru-dpd-mdict.mdx"
        self.mdict_mdd_path = base_dir / "exporter/share/ru-dpd-mdict.mdd"
        self.grammar_dict_mdx_path = base_dir / "exporter/share/ru-dpd-grammar-mdict.mdx"
        self.grammar_dict_mdd_path = base_dir / "exporter/share/ru-dpd-grammar-mdict.mdd"
        self.deconstructor_mdx_path = base_dir / "exporter/share/ru-dpd-deconstructor-mdict.mdx"
        self.deconstructor_mdd_path = base_dir / "exporter/share/ru-dpd-deconstructor-mdict.mdd"



        # /goldendict/ru_components/templates
        self.templates_dir = base_dir / "exporter/goldendict/ru_components/templates"

        self.dpd_header_templ_path = base_dir / "exporter/goldendict/ru_components/templates/dpd_ru_header.html"
        self.dpd_header_plain_templ_path = base_dir / "exporter/goldendict/ru_components/templates/dpd_ru_header_plain.html"
        self.root_header_templ_path = base_dir / "exporter/goldendict/ru_components/templates/root_header_ru.html"
        self.deconstructor_header_templ_path = base_dir / "exporter/goldendict/templates/deconstructor_header.html"
        self.grammar_dict_header_templ_path = base_dir / "exporter/goldendict/templates/grammar_dict_header.html"

        self.dpd_definition_templ_path = base_dir / "exporter/goldendict/ru_components/templates/dpd_ru_definition.html"
        self.button_box_templ_path = base_dir / "exporter/goldendict/ru_components/templates/dpd_ru_button_box.html"
        self.grammar_templ_path = base_dir / "exporter/goldendict/ru_components/templates/dpd_ru_grammar.html"
        self.example_templ_path = base_dir / "exporter/goldendict/ru_components/templates/dpd_ru_example.html"
        self.sbs_example_templ_path = base_dir / "exporter/goldendict/templates/sbs_example.html"
        self.inflection_templ_path = base_dir / "exporter/goldendict/ru_components/templates/dpd_ru_inflection.html"
        self.family_root_templ_path = base_dir / "exporter/goldendict/ru_components/templates/dpd_ru_family_root.html"
        self.family_word_templ_path = base_dir / "exporter/goldendict/ru_components/templates/dpd_ru_family_word.html"
        self.family_compound_templ_path = base_dir / "exporter/goldendict/ru_components/templates/dpd_ru_family_compound.html"
        self.family_idiom_templ_path = base_dir / "exporter/goldendict/ru_components/templates/dpd_ru_family_idiom.html"
        self.family_set_templ_path = base_dir / "exporter/goldendict/ru_components/templates/dpd_ru_family_set.html"
        self.frequency_templ_path = base_dir / "exporter/goldendict/ru_components/templates/dpd_ru_frequency.html"
        self.feedback_templ_path = base_dir / "exporter/goldendict/ru_components/templates/dpd_ru_feedback.html"
        self.variant_templ_path = base_dir / "exporter/goldendict/ru_components/templates/dpd_ru_variant_reading.html"
        self.spelling_templ_path = base_dir / "exporter/goldendict/ru_components/templates/dpd_ru_spelling_mistake.html"
        
        # /goldendict/ru_components/templates - root
        self.root_definition_templ_path = base_dir / "exporter/goldendict/ru_components/templates/root_definition_ru.html"
        self.root_button_templ_path = base_dir / "exporter/goldendict/ru_components/templates/root_buttons_ru.html"
        self.root_info_templ_path = base_dir / "exporter/goldendict/ru_components/templates/root_info_ru.html"
        self.root_matrix_templ_path = base_dir / "exporter/goldendict/ru_components/templates/root_matrix_ru.html"
        self.root_families_templ_path = base_dir / "exporter/goldendict/ru_components/templates/root_families_ru.html"

        # /goldendict/ru_components/templates - other
        self.epd_templ_path = base_dir / "exporter/goldendict/ru_components/templates/rpd.html"
        self.abbrev_templ_path = base_dir / "exporter/goldendict/ru_components/templates/help_abbrev.html"
        self.help_templ_path = base_dir / "exporter/goldendict/ru_components/templates/help_help.html"
        self.deconstructor_templ_path = base_dir / "exporter/goldendict/ru_components/templates/deconstructor_ru.html"

        # /goldendict/ru_components/icon
        self.icon_bmp_path = base_dir / "exporter/goldendict/ru_components/icon/book.bmp"
        self.icon_path = base_dir / "exporter/goldendict/ru_components/icon/book.bmp"

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

