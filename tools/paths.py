"""All file paths that get used in the Project."""

import os
from typing import Optional
from pathlib import Path


class ProjectPaths:

    def __init__(self, base_dir: Optional[Path] = None, create_dirs=True):

        if base_dir is None:
            # The current working directory of the shell.
            base_dir = Path(os.path.abspath("."))

        # root
        self.dpd_db_path = base_dir / "dpd.db"
        self.pyproject_path = base_dir / "pyproject.toml"

        # backup_tsv
        self.pali_root_path = base_dir / "db/backup_tsv/dpd_roots.tsv"
        self.pali_word_path = base_dir / "db/backup_tsv/dpd_headwords.tsv"
        self.ru_root_path = base_dir / "db/backup_tsv/ru_roots.tsv"
        self.russian_path = base_dir / "db/backup_tsv/russian.tsv"
        self.sbs_path = base_dir / "db/backup_tsv/sbs.tsv"

        # db/bold_definitions
        self.bold_definitions_json_path = base_dir / "db/bold_definitions/bold_definitions.json"
        self.bold_definitions_tsv_path = base_dir / "db/bold_definitions/bold_definitions.tsv"

        # exporter/kindle/
        self.epub_dir = base_dir / "exporter/kindle/epub/"
        self.kindlegen_path = base_dir / "exporter/kindle/kindlegen"

        # exporter/kindle/epub
        self.epub_abbreviations_path = base_dir / "exporter/kindle/epub/OEBPS/Text/abbreviations.xhtml"
        self.epub_content_opf_path = base_dir / "exporter/kindle/epub/OEBPS/content.opf"
        self.epub_text_dir = base_dir / "exporter/kindle/epub/OEBPS/Text"
        self.epub_titlepage_path = base_dir / "exporter/kindle/epub/OEBPS/Text/titlepage.xhtml"

        # exporter/kindle/templates
        self.ebook_abbrev_entry_templ_path = base_dir / "exporter/kindle/templates/ebook_abbreviation_entry.html"
        self.ebook_content_opf_templ_path = base_dir / "exporter/kindle/templates/ebook_content_opf.html"
        self.ebook_deconstructor_templ_path = base_dir / "exporter/kindle/templates/ebook_deconstructor_entry.html"
        self.ebook_entry_templ_path = base_dir / "exporter/kindle/templates/ebook_entry.html"
        self.ebook_example_templ_path = base_dir / "exporter/kindle/templates/ebook_example.html"
        self.ebook_grammar_templ_path = base_dir / "exporter/kindle/templates/ebook_grammar.html"
        self.ebook_letter_templ_path = base_dir / "exporter/kindle/templates/ebook_letter.html"
        self.ebook_title_page_templ_path = base_dir / "exporter/kindle/templates/ebook_titlepage.html"

        # exporter/css
        self.dpd_css_path = base_dir / "exporter/goldendict/css/dpd.css"
        self.deconstructor_css_path = base_dir / "exporter/goldendict/css/deconstructor.css"
        self.grammar_css_path = base_dir / "exporter/goldendict/css/grammar.css"
        # self.roots_css_path = base_dir / "exporter/goldendict/css/roots.css"
        # self.epd_css_path = base_dir / "exporter/goldendict/css/epd.css"
        # self.help_css_path = base_dir / "exporter/goldendict/css/help.css"
        # self.variant_spelling_css_path = base_dir / "exporter/goldendict/css/variant_spelling.css"

        # exporter/goldendict/help/
        self.abbreviations_tsv_path = base_dir / "exporter/goldendict/help/abbreviations.tsv"
        self.bibliography_tsv_path = base_dir / "exporter/goldendict/help/bibliography.tsv"
        self.help_tsv_path = base_dir / "exporter/goldendict/help/help.tsv"
        self.thanks_tsv_path = base_dir / "exporter/goldendict/help/thanks.tsv"

        # exporter/goldendict/javascript/
        self.buttons_js_path = base_dir / "exporter/goldendict/javascript/buttons.js"
        self.family_compound_json = base_dir / "exporter/goldendict/javascript/family_compound_json.js"
        self.family_compound_template_js = base_dir / "exporter/goldendict/javascript/family_compound_template.js"
        self.family_idiom_json = base_dir / "exporter/goldendict/javascript/family_idiom_json.js"
        self.family_idiom_template_js = base_dir / "exporter/goldendict/javascript/family_idiom_template.js"
        self.family_root_json = base_dir / "exporter/goldendict/javascript/family_root_json.js"
        self.family_root_template_js = base_dir / "exporter/goldendict/javascript/family_root_template.js"
        self.family_set_json = base_dir / "exporter/goldendict/javascript/family_set_json.js"
        self.family_set_template_js = base_dir / "exporter/goldendict/javascript/family_set_template.js"
        self.family_word_json = base_dir / "exporter/goldendict/javascript/family_word_json.js"
        self.family_word_template_js = base_dir / "exporter/goldendict/javascript/family_word_template.js"
        self.feedback_template_js = base_dir / "exporter/goldendict/javascript/feedback_template.js"
        self.frequency_template_js = base_dir / "exporter/goldendict/javascript/frequency_template.js"
        self.main_js_path = base_dir / "exporter/goldendict/javascript/main.js"
        self.sorter_js_path = base_dir / "exporter/goldendict/javascript/sorter.js"

        # exporter/share
        self.deconstructor_goldendict_dir = base_dir / "exporter/share/dpd-deconstructor/"
        self.dpd_epub_path = base_dir / "exporter/share/dpd-kindle.epub"
        self.dpd_goldendict_dir = base_dir / "exporter/share/dpd/"
        self.dpd_goldendict_zip_path = base_dir / "exporter/share/dpd-goldendict.zip"
        self.dpd_mdict_zip_path = base_dir / "exporter/share/dpd-mdict.zip"
        self.dpd_mobi_path = base_dir / "exporter/share/dpd-kindle.mobi"
        self.grammar_dict_goldendict_dir = base_dir / "exporter/share/dpd-grammar/"
        self.share_dir = base_dir / "exporter/share"
        self.summary_md_path = base_dir / "exporter/share/summary.md"

        # exporter/share/mdict
        self.deconstructor_mdd_path = base_dir / "exporter/share/dpd-deconstructor-mdict.mdd"
        self.deconstructor_mdx_path = base_dir / "exporter/share/dpd-deconstructor-mdict.mdx"
        self.grammar_dict_mdd_path = base_dir / "exporter/share/dpd-grammar-mdict.mdd"
        self.grammar_dict_mdx_path = base_dir / "exporter/share/dpd-grammar-mdict.mdx"
        self.mdict_mdd_path = base_dir / "exporter/share/dpd-mdict.mdd"
        self.mdict_mdx_path = base_dir / "exporter/share/dpd-mdict.mdx"

        # exporter/deconstructor/templates
        self.deconstructor_header_templ_path = base_dir / "exporter/deconstructor/templates/deconstructor_header.html"
        self.deconstructor_templ_path = base_dir / "exporter/deconstructor/templates/deconstructor.html"

        # exporter/templates
        self.button_box_templ_path = base_dir / "exporter/goldendict/templates/dpd_button_box.html"
        self.dpd_definition_templ_path = base_dir / "exporter/goldendict/templates/dpd_definition.html"
        self.dpd_header_plain_templ_path = base_dir / "exporter/goldendict/templates/dpd_header_plain.html"
        self.dpd_header_templ_path = base_dir / "exporter/goldendict/templates/dpd_header.html"
        self.example_templ_path = base_dir / "exporter/goldendict/templates/dpd_example.html"
        self.family_compound_templ_path = base_dir / "exporter/goldendict/templates/dpd_family_compound.html"
        self.family_idiom_templ_path = base_dir / "exporter/goldendict/templates/dpd_family_idiom.html"
        self.family_root_templ_path = base_dir / "exporter/goldendict/templates/dpd_family_root.html"
        self.family_set_templ_path = base_dir / "exporter/goldendict/templates/dpd_family_set.html"
        self.family_word_templ_path = base_dir / "exporter/goldendict/templates/dpd_family_word.html"
        self.feedback_templ_path = base_dir / "exporter/goldendict/templates/dpd_feedback.html"
        self.frequency_templ_path = base_dir / "exporter/goldendict/templates/dpd_frequency.html"
        self.grammar_dict_header_templ_path = base_dir / "exporter/goldendict/templates/grammar_dict_header.html"
        self.grammar_templ_path = base_dir / "exporter/goldendict/templates/dpd_grammar.html"
        self.inflection_templ_path = base_dir / "exporter/goldendict/templates/dpd_inflection.html"
        self.root_header_templ_path = base_dir / "exporter/goldendict/templates/root_header.html"
        self.sbs_example_templ_path = base_dir / "exporter/goldendict/templates/sbs_example.html"
        self.spelling_templ_path = base_dir / "exporter/goldendict/templates/dpd_spelling_mistake.html"
        self.templates_dir = base_dir / "exporter/templates"
        self.variant_templ_path = base_dir / "exporter/goldendict/templates/dpd_variant_reading.html"

        # FIXME delete these and whatever uses them
        # exporter/jinja templates
        self.complete_word_templ_path = base_dir / "exporter/templates_jinja/dpd_complete_word.html"
        self.jinja_templates_dir = base_dir / "exporter/templates_jinja/"
        self.temp_html_file_path = base_dir / "temp/temp_html_file.html"

        # exporter/goldendict/templates - root
        self.root_button_templ_path = base_dir / "exporter/goldendict/templates/root_buttons.html"
        self.root_definition_templ_path = base_dir / "exporter/goldendict/templates/root_definition.html"
        self.root_families_templ_path = base_dir / "exporter/goldendict/templates/root_families.html"
        self.root_info_templ_path = base_dir / "exporter/goldendict/templates/root_info.html"
        self.root_matrix_templ_path = base_dir / "exporter/goldendict/templates/root_matrix.html"

        # exporter/goldendict/templates - other
        self.abbrev_templ_path = base_dir / "exporter/goldendict/templates/help_abbrev.html"
        self.epd_templ_path = base_dir / "exporter/goldendict/templates/epd.html"
        self.help_templ_path = base_dir / "exporter/goldendict/templates/help_help.html"

        # exporter/tpr
        self.tpr_deconstructor_tsv_path = base_dir / "exporter/tpr/output/deconstructor.tsv"
        self.tpr_dpd_tsv_path = base_dir / "exporter/tpr/output/dpd.tsv"
        self.tpr_i2h_tsv_path = base_dir / "exporter/tpr/output/i2h.tsv"
        self.tpr_output_dir = base_dir / "exporter/tpr/output"
        self.tpr_sql_file_path = base_dir / "exporter/tpr/output/dpd.sql"

        # exporter/grammar_dict/output
        self.grammar_dict_output_dir = base_dir / "exporter/grammar_dict/output"
        self.grammar_dict_output_html_dir = base_dir / "exporter/grammar_dict/output/html"
        self.grammar_dict_pickle_path = base_dir / "exporter/grammar_dict/output/grammar_dict_pickle"
        self.grammar_dict_tsv_path = base_dir / "exporter/grammar_dict/output/grammar_dict.tsv"


        # exporter/goldendict/icon
        self.icon_path = base_dir / "exporter/goldendict/icon/favicon.ico"
        self.icon_bmp_path = base_dir / "exporter/goldendict/icon/dpd.bmp"

        # exporter/other_dictionaries/css
        self.cone_css_path = base_dir / "exporter/other_dictionaries/code/cone/cone.css"
        self.dpr_css_path = base_dir / "exporter/other_dictionaries/code/dpr/dpr.css/"
        self.whitney_css_path = base_dir / "exporter/other_dictionaries/code/whitney/whitney.css/"

        # exporter/other_dictionaries/source
        self.bhs_source_path = base_dir / "exporter/other_dictionaries/code/bhs/source/bhs.xml"
        self.cone_front_matter_path = base_dir / "exporter/other_dictionaries/code/cone/source/cone_front_matter.json"
        self.cone_source_path = base_dir / "exporter/other_dictionaries/code/cone/source/cone_dict.json"
        self.cpd_source_path = base_dir / "exporter/other_dictionaries/code/cpd/source/en-critical.json"
        self.dpr_source_path = base_dir / "exporter/other_dictionaries/code/dpr/source/dpr.json"
        self.eng_sin_source_path = base_dir / "exporter/other_dictionaries/code/sin_eng_sin/source/english-sinhala.tab"
        self.mw_source_path = base_dir / "exporter/other_dictionaries/code/mw/source/mw_from_simsapa.json"
        self.peu_source_path = base_dir / "exporter/other_dictionaries/code/peu/source/latest.json"
        self.sin_eng_source_path = base_dir / "exporter/other_dictionaries/code/sin_eng_sin/source/sinhala-english.tab"
        self.vri_source_path = base_dir / "exporter/other_dictionaries/code/vri/source/vri.csv"
        self.whitney_source_dir = base_dir / "exporter/other_dictionaries/code/whitney/source/"

        # exporter/other_dictionaries/goldendict
        self.bhs_gd_path = base_dir / "exporter/other_dictionaries/goldendict/"
        self.cone_gd_path = base_dir / "exporter/other_dictionaries/goldendict/"
        self.cpd_gd_path = base_dir / "exporter/other_dictionaries/goldendict/"
        self.dpr_gd_path = base_dir / "exporter/other_dictionaries/goldendict/"
        self.mw_gd_path = base_dir / "exporter/other_dictionaries/goldendict/"
        self.peu_gd_path = base_dir / "exporter/other_dictionaries/goldendict/"
        self.simsapa_gd_path = base_dir / "exporter/other_dictionaries/goldendict/"
        self.sin_eng_sin_gd_path = base_dir / "exporter/other_dictionaries/goldendict/"
        self.vri_gd_path = base_dir / "exporter/other_dictionaries/goldendict/vri.zip"
        self.whitney_gd_path = base_dir / "exporter/other_dictionaries/goldendict/"

        # exporter/other_dictionaries/json
        self.bhs_json_path = base_dir / "exporter/other_dictionaries/json/bhs.json"
        self.cone_json_path = base_dir / "exporter/other_dictionaries/json/cone.json"
        self.cpd_json_path = base_dir / "exporter/other_dictionaries/json/cpd.json"
        self.dpr_json_path = base_dir / "exporter/other_dictionaries/json/dpr.json"
        self.mw_json_path = base_dir / "exporter/other_dictionaries/json/mw.json"
        self.peu_json_path = base_dir / "exporter/other_dictionaries/json/peu.json"
        self.simsapa_json_path = base_dir / "exporter/other_dictionaries/json/simsapa.json"
        self.sin_eng_sin_json_path = base_dir / "exporter/other_dictionaries/json/sin_eng_sin.json"
        self.vri_json_path = base_dir / "exporter/other_dictionaries/json/vri.json"
        self.whitney_json_path = base_dir / "exporter/other_dictionaries/json/whitney.json"

        # exporter/other_dictionaries/mdict
        self.bhs_mdict_path = base_dir / "exporter/other_dictionaries/mdict/"
        self.cone_mdict_path = base_dir / "exporter/other_dictionaries/mdict/"
        self.cpd_mdict_path = base_dir / "exporter/other_dictionaries/mdict/"
        self.dpr_mdict_path = base_dir / "exporter/other_dictionaries/mdict/"
        self.mw_mdict_path = base_dir / "exporter/other_dictionaries/mdict/"
        self.peu_mdict_path = base_dir / "exporter/other_dictionaries/mdict/"
        self.simsapa_mdict_path = base_dir / "exporter/other_dictionaries/mdict/"
        self.sin_eng_sin_mdict_path = base_dir / "exporter/other_dictionaries/mdict/"
        self.vri_mdict_path = base_dir / "exporter/other_dictionaries/mdict/vri.mdx"
        self.whitney_mdict_path = base_dir / "exporter/other_dictionaries/mdict/"

        # exporter/pdf
        self.typst_data_path = base_dir / "exporter/pdf/typst_data.typ"
        self.typst_pdf_path = base_dir / "exporter/share/dpd.pdf"
        self.typst_lite_data_path = base_dir / "exporter/pdf/typst_data_lite.typ"
        self.typst_lite_pdf_path = base_dir / "exporter/share/dpd.pdf"
        self.typst_lite_zip_path = base_dir / "exporter/share/dpd-pdf.zip"

        # db/frequency/output
        self.ebt_raw_text_path = base_dir / "db/frequency/output/raw_text/ebts.txt"
        self.ebt_word_count_path = base_dir / "db/frequency/output/word_count/ebts.csv"
        self.freq_html_dir = base_dir / "db/frequency/output/html/"
        self.frequency_output_dir = base_dir / "db/frequency/output/"
        self.raw_text_dir = base_dir / "db/frequency/output/raw_text/"
        self.tipitaka_raw_text_path = base_dir / "db/frequency/output/raw_text/tipitaka.txt"
        self.tipitaka_word_count_path = base_dir / "db/frequency/output/word_count/tipitaka.csv"
        self.word_count_dir = base_dir / "db/frequency/output/word_count"

        # gui
        self.additions_tsv_path = base_dir / "gui/additions.tsv"
        self.additions_pickle_path = base_dir / "gui/additions"
        self.corrections_tsv_path = base_dir / "gui/corrections.tsv"
        self.delated_words_history_pth = base_dir / "gui/delated_words_history.tsv"
        self.pass2_checked_path = base_dir / "gui/pass2_checked.json"

        # gui/stash
        self.daily_record_path = base_dir / "gui/stash/daily_record"
        self.example_stash_path = base_dir / "gui/stash/example"
        self.save_state_path = base_dir / "gui/stash/gui_state"
        self.stash_dir = base_dir / "gui/stash/"
        self.stash_path = base_dir / "gui/stash/stash"

        # db/inflections/
        self.inflection_templates_path = base_dir / "db/inflections/inflection_templates.xlsx"

        # resources/bw/js
        self.tbw_i2h_js_path = base_dir / "resources/bw2/js/dpd_i2h.js"
        self.tbw_dpd_ebts_js_path = base_dir / "resources/bw2/js/dpd_ebts.js"
        self.tbw_deconstructor_js_path = base_dir / "resources/bw2/js/dpd_deconstructor.js"

        # resources/sc-data
        self.sc_data_dir = base_dir / "resources/sc-data/sc_bilara_data/root/pli/ms/"
        self.sc_data_dpd_dir = base_dir / "resources/sc-data/dpd/"

        self.sc_i2h_js_path = base_dir / "resources/sc-data/dpd/dpd_i2h.js"
        self.sc_i2h_json_path = base_dir / "resources/sc-data/dpd/dpd_i2h.json"

        self.sc_dpd_ebts_js_path = base_dir / "resources/sc-data/dpd/dpd_ebts.js"
        self.sc_dpd_ebts_json_path = base_dir / "resources/sc-data/dpd/dpd_ebts.json"

        self.sc_deconstructor_js_path = base_dir / "resources/sc-data/dpd/dpd_deconstructor.js"
        self.sc_deconstructor_json_path = base_dir / "resources/sc-data/dpd/dpd_deconstructor.json"

        # resources/tipitaka-xml
        self.cst_txt_dir = base_dir / "resources/tipitaka-xml/romn_txt/"
        self.cst_xml_dir = base_dir / "resources/tipitaka-xml/deva/"
        self.cst_xml_roman_dir = base_dir / "resources/tipitaka-xml/romn/"

        # resources/bjt
        self.bjt_dir = base_dir / "resources/bjt/public/static/"
        self.bjt_sinhala_dir = base_dir / "resources/bjt/public/static/text/"
        self.bjt_roman_json_dir = base_dir / "resources/bjt/public/static/roman_json/"
        self.bjt_roman_txt_dir = base_dir / "resources/bjt/public/static/roman_txt/"
        self.bjt_books_dir = base_dir / "resources/bjt/public/static/books/"

        # resources/other_pali_texts
        self.other_pali_texts_dir = base_dir / "resources/other_pali_texts"

        # resources/tpr
        self.tpr_beta_path = base_dir / "resources/tpr_downloads/release_zips/dpd_beta.zip"
        self.tpr_download_list_path = base_dir / "resources/tpr_downloads/download_source_files/download_list.json"
        self.tpr_release_path = base_dir / "resources/tpr_downloads/release_zips/dpd.zip"

        # resources/deconstructor_output repo
        self.deconstructor_output_json = base_dir / "resources/deconstructor_output/deconstructor_output.json"
        self.deconstructor_output_tar_path = base_dir / "resources/deconstructor_output/deconstructor_output.json.tar.gz"
        self.deconstructor_output_dir = base_dir / "resources/deconstructor_output/"

        # db/deconstructor/assets
        self.all_inflections_set_path = base_dir / "db/deconstructor/assets/all_inflections_set"
        self.matches_dict_path = base_dir / "db/deconstructor/assets/matches_dict"
        self.neg_inflections_set_path = base_dir / "db/deconstructor/assets/neg_inflections_set"
        self.sandhi_assets_dir = base_dir / "db/deconstructor/assets"
        self.text_set_path = base_dir / "db/deconstructor/assets/text_set"
        self.unmatched_set_path = base_dir / "db/deconstructor/assets/unmatched_set"

        # db/deconstructor/output
        self.matches_do_path = base_dir / "db/deconstructor/output_do/matches.tsv"
        self.matches_path = base_dir / "db/deconstructor/output/matches.tsv"
        self.matches_sorted = base_dir / "db/deconstructor/output/matches_sorted.tsv"
        self.process_path = base_dir / "db/deconstructor/output/process.tsv"
        self.rule_counts_path = base_dir / "db/deconstructor/output/rule_counts/rule_counts.tsv"
        self.sandhi_dict_df_path = base_dir / "db/deconstructor/output/sandhi_dict_df.tsv"
        self.sandhi_dict_path = base_dir / "db/deconstructor/output/sandhi_dict"
        self.sandhi_log_path = base_dir / "db/deconstructor/output/logfile.log"
        self.sandhi_output_dir = base_dir / "db/deconstructor/output/"
        self.sandhi_output_do_dir = base_dir / "db/deconstructor/output_do/"
        self.sandhi_timer_path = base_dir / "db/deconstructor/output/timer.tsv"
        self.unmatched_path = base_dir / "db/deconstructor/output/unmatched.tsv"

        # db/deconstructor/output/rule_counts
        self.rule_counts_dir = base_dir / "db/deconstructor/output/rule_counts/"

        # db/deconstructor/output/letters
        self.letters_dir = base_dir / "db/deconstructor/output/letters/"
        self.letters = base_dir / "db/deconstructor/output/letters/letters.tsv"
        self.letters1 = base_dir / "db/deconstructor/output/letters/letters1.tsv"
        self.letters2 = base_dir / "db/deconstructor/output/letters/letters2.tsv"
        self.letters3 = base_dir / "db/deconstructor/output/letters/letters3.tsv"
        self.letters4 = base_dir / "db/deconstructor/output/letters/letters4.tsv"
        self.letters5 = base_dir / "db/deconstructor/output/letters/letters5.tsv"
        self.letters6 = base_dir / "db/deconstructor/output/letters/letters6.tsv"
        self.letters7 = base_dir / "db/deconstructor/output/letters/letters7.tsv"
        self.letters8 = base_dir / "db/deconstructor/output/letters/letters8.tsv"
        self.letters9 = base_dir / "db/deconstructor/output/letters/letters9.tsv"
        self.letters10 = base_dir / "db/deconstructor/output/letters/letters10plus.tsv"

        # shared_data/deconstructor
        self.decon_manual_corrections = base_dir / "shared_data/deconstructor/manual_corrections.tsv"
        self.decon_exceptions = base_dir / "shared_data/deconstructor/exceptions.tsv"
        self.decon_checked = base_dir / "shared_data/deconstructor/checked.csv"
        self.sandhi_rules_path = base_dir / "shared_data/deconstructor/sandhi_rules.tsv"
        self.spelling_mistakes_path = base_dir / "shared_data/deconstructor/spelling_mistakes.tsv"
        self.variant_readings_path = base_dir / "shared_data/deconstructor/variant_readings.tsv"

        # db/sanskrit
        self.root_families_sanskrit_path = base_dir / "db/sanskrit/root_families_sanskrit.tsv"

        # share
        self.all_tipitaka_words_path = base_dir / "shared_data/all_tipitaka_words"
        self.changed_headwords_path = base_dir / "shared_data/changed_headwords"
        self.headword_stem_pattern_dict_path = base_dir / "shared_data/headword_stem_pattern_dict"
        self.inflection_templates_pickle_path = base_dir / "shared_data/inflection_templates"
        self.inflections_from_translit_json_path = base_dir / "shared_data/inflections_from_translit.json"
        self.inflections_to_translit_json_path = base_dir / "shared_data/inflections_to_translit.json"
        self.lookup_from_translit_path = base_dir / "shared_data/lookup_from_translit.json"
        self.lookup_to_translit_path = base_dir / "shared_data/lookup_to_translit.json"
        self.template_changed_path = base_dir / "shared_data/changed_templates"

        # share/frequency
        self.cst_file_freq = base_dir / "shared_data/frequency/cst_file_freq.json"
        self.cst_wordlist = base_dir / "shared_data/frequency/cst_wordlist.json"
        
        self.bjt_file_freq = base_dir / "shared_data/frequency/bjt_file_freq.json"
        self.bjt_wordlist = base_dir / "shared_data/frequency/bjt_wordlist.json"

        self.sya_file_freq = base_dir / "shared_data/frequency/sya_file_freq.json"
        self.sya_wordlist = base_dir / "shared_data/frequency/sya_wordlist.json"

        self.sc_file_freq = base_dir / "shared_data/frequency/sc_file_freq.json"
        self.sc_wordlist = base_dir / "shared_data/frequency/sc_wordlist.json"

        # temp
        self.temp_dir = base_dir / "temp/"

        # db_tests/
        self.antonym_dict_path = base_dir / "db_tests/test_antonyms.json"
        self.bahubbihi_dict_path = base_dir / "db_tests/test_bahubbihis.json"
        self.bold_example_path = base_dir / "db_tests/test_bold.json"
        self.compound_type_path = base_dir / "db_tests/add_compound_type.tsv"
        self.digu_json_path = base_dir / "db_tests/test_digu.json"
        self.hyphenations_dict_path = base_dir / "db_tests/test_hyphenations.json"
        self.hyphenations_scratchpad_path = base_dir / "db_tests/test_hyphenations.txt"
        self.idioms_exceptions_dict = base_dir / "db_tests/test_idioms.json"
        self.internal_tests_path = base_dir / "db_tests/tests_internal.tsv"
        self.maha_exceptions_list = base_dir / "db_tests/test_maha_exceptions.json"
        self.neg_compound_exceptions = base_dir / "db_tests/test_neg_compound_exceptions.json"
        self.phonetic_changes_path = base_dir / "db_tests/add_phonetic_changes.tsv"
        self.phonetic_changes_vowels_path = base_dir / "db_tests/add_phonetic_changes_vowels.tsv"
        self.sukha_dukkha_finder_path = base_dir / "db_tests/test_sukha_dukkha_finder.json"
        self.syn_var_exceptions_old_path = base_dir / "db_tests/add_synonym_variant_exceptions"
        self.syn_var_exceptions_path = base_dir / "db_tests/add_synonym_variant.json"
        self.wf_exceptions_list = base_dir / "db_tests/add_word_family_exceptions"

        # tools
        self.user_dict_path = base_dir / "tools/user_dictionary.txt"
        self.uposatha_day_ini = base_dir / "tools/uposatha_day.ini"

        # .. external
        self.bibliography_md_path = base_dir / "../digitalpalidictionary-website-source/src/bibliography.md"
        self.old_dpd_full_path = base_dir / "../csvs/dpd-full.csv"
        self.old_roots_csv_path = base_dir / "../csvs/roots.csv"
        self.thanks_md_path = base_dir / "../digitalpalidictionary-website-source/src/thanks.md"

        # go_modules
        self.go_deconstructor_output_dir = base_dir / "go_modules/deconstructor/output"

        if create_dirs:
            self.create_dirs()

    def create_dirs(self):
        for d in [
            self.bjt_books_dir,
            self.bjt_roman_json_dir,
            self.bjt_roman_txt_dir,
            self.cst_txt_dir,
            self.cst_xml_roman_dir,
            self.epub_text_dir,
            self.freq_html_dir,
            self.frequency_output_dir,
            self.go_deconstructor_output_dir,
            self.grammar_dict_output_dir,
            self.grammar_dict_output_html_dir,
            self.letters_dir,
            self.raw_text_dir,
            self.rule_counts_dir,
            self.sandhi_assets_dir,
            self.sandhi_output_dir,
            self.sandhi_output_do_dir,
            self.share_dir,
            self.stash_dir,
            self.temp_dir,
            self.tpr_output_dir,
            self.word_count_dir,
        ]:
            d.mkdir(parents=True, exist_ok=True)
