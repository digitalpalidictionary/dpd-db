"""All file paths that get used in the Project."""

import os
from typing import Optional
from pathlib import Path

class ProjectPaths:

    def __init__(self, base_dir: Optional[Path] = None, create_dirs = True):

        if base_dir is None:
            # The current working directory of the shell.
            base_dir = Path(os.path.abspath("."))

        # root
        self.dpd_db_path = base_dir / "dpd.db"
        self.pyproject_path = base_dir / "pyproject.toml"

        # backup_tsv
        self.pali_word_path = base_dir / "db/backup_tsv/dpd_headwords.tsv"
        self.pali_root_path = base_dir / "db/backup_tsv/dpd_roots.tsv"
        self.russian_path = base_dir / "db/backup_tsv/russian.tsv"
        self.sbs_path = base_dir / "db/backup_tsv/sbs.tsv"
        self.ru_root_path = base_dir / "db/backup_tsv/ru_roots.tsv"

        # db/bold_definitions
        self.bold_definitions_tsv_path = base_dir / "db/bold_definitions/bold_definitions.tsv"
        self.bold_definitions_json_path = base_dir / "db/bold_definitions/bold_definitions.json"

        # exporter/ebook/
        self.epub_dir = base_dir / "exporter/ebook/epub/"
        self.epub_dir = base_dir / "exporter/ebook/epub/"
        self.kindlegen_path = base_dir / "exporter/ebook/kindlegen"

        # exporter/ebook/epub
        self.epub_text_dir = base_dir / "exporter/ebook/epub/OEBPS/Text"
        self.epub_content_opf_path = base_dir / "exporter/ebook/epub/OEBPS/content.opf"
        self.epub_abbreviations_path = base_dir / "exporter/ebook/epub/OEBPS/Text/abbreviations.xhtml"
        self.epub_titlepage_path = base_dir / "exporter/ebook/epub/OEBPS/Text/titlepage.xhtml"

        # exporter/ebook/templates
        self.ebook_letter_templ_path = base_dir / "exporter/ebook/templates/ebook_letter.html"
        self.ebook_entry_templ_path = base_dir / "exporter/ebook/templates/ebook_entry.html"
        self.ebook_deconstructor_templ_path = base_dir / "exporter/ebook/templates/ebook_deconstructor_entry.html"
        self.ebook_grammar_templ_path = base_dir / "exporter/ebook/templates/ebook_grammar.html"
        self.ebook_example_templ_path = base_dir / "exporter/ebook/templates/ebook_example.html"
        self.ebook_abbrev_entry_templ_path = base_dir / "exporter/ebook/templates/ebook_abbreviation_entry.html"
        self.ebook_title_page_templ_path = base_dir / "exporter/ebook/templates/ebook_titlepage.html"
        self.ebook_content_opf_templ_path = base_dir / "exporter/ebook/templates/ebook_content_opf.html"

        # exporter/css
        self.dpd_css_path = base_dir / "exporter/goldendict/css/dpd.css"
        self.deconstructor_css_path = base_dir / "exporter/goldendict/css/deconstructor.css"
        self.grammar_css_path = base_dir / "exporter/goldendict/css/grammar.css"
        # self.roots_css_path = base_dir / "exporter/goldendict/css/roots.css"
        # self.epd_css_path = base_dir / "exporter/goldendict/css/epd.css"
        # self.help_css_path = base_dir / "exporter/goldendict/css/help.css"
        # self.variant_spelling_css_path = base_dir / "exporter/goldendict/css/variant_spelling.css"

        # exporter/goldendict/help/
        self.abbreviations_tsv_path = base_dir / "exporter/goldendict/help//abbreviations.tsv"
        self.help_tsv_path = base_dir / "exporter/goldendict/help//help.tsv"
        self.bibliography_tsv_path = base_dir / "exporter/goldendict/help//bibliography.tsv"
        self.thanks_tsv_path = base_dir / "exporter/goldendict/help//thanks.tsv"

        # exporter/goldendict/javascript/
        self.buttons_js_path = base_dir / "exporter/goldendict/javascript//buttons.js"
        self.sorter_js_path = base_dir / "exporter/goldendict/javascript//sorter.js"

        # exporter/goldendict/json/
        self.family_compound_json = base_dir / "exporter/goldendict/javascript/family_compound_json.js"
        self.family_idiom_json = base_dir / "exporter/goldendict/javascript/family_idiom_json.js"
        self.family_root_json = base_dir / "exporter/goldendict/javascript/family_root_json.js"
        self.family_set_json = base_dir / "exporter/goldendict/javascript/family_set_json.js"
        self.family_word_json = base_dir / "exporter/goldendict/javascript/family_word_json.js"

        # exporter/share
        self.share_dir = base_dir / "exporter/share"
        
        self.dpd_goldendict_dir = base_dir / "exporter/share/dpd/"
        self.grammar_dict_goldendict_dir = base_dir / "exporter/share/dpd-grammar/"
        self.deconstructor_goldendict_dir = base_dir / "exporter/share/dpd-deconstructor/"
        
        self.dpd_mobi_path = base_dir / "exporter/share/dpd-kindle.mobi"
        self.dpd_epub_path = base_dir / "exporter/share/dpd-kindle.epub"
        
        self.dpd_goldendict_zip_path = base_dir / "exporter/share/dpd-goldendict.zip"
        self.dpd_mdict_zip_path = base_dir / "exporter/share/dpd-mdict.zip"
        self.summary_md_path = base_dir / "exporter/share/summary.md"

        # exporter/share/mdict
        self.mdict_mdx_path = base_dir / "exporter/share/dpd-mdict.mdx"
        self.mdict_mdd_path = base_dir / "exporter/share/dpd-mdict.mdd"
        self.grammar_dict_mdx_path = base_dir / "exporter/share/dpd-grammar-mdict.mdx"
        self.grammar_dict_mdd_path = base_dir / "exporter/share/dpd-grammar-mdict.mdd"
        self.deconstructor_mdx_path = base_dir / "exporter/share/dpd-deconstructor-mdict.mdx"
        self.deconstructor_mdd_path = base_dir / "exporter/share/dpd-deconstructor-mdict.mdd"



        # exporter/templates
        self.templates_dir = base_dir / "exporter/templates"
        self.dpd_header_templ_path = base_dir / "exporter/goldendict/templates/dpd_header.html"
        self.root_header_templ_path = base_dir / "exporter/goldendict/templates/root_header.html"
        self.header_plain_templ_path = base_dir / "exporter/goldendict/templates/header_plain.html"
        self.dpd_definition_templ_path = base_dir / "exporter/goldendict/templates/dpd_definition.html"
        self.button_box_templ_path = base_dir / "exporter/goldendict/templates/dpd_button_box.html"
        self.grammar_templ_path = base_dir / "exporter/goldendict/templates/dpd_grammar.html"
        self.example_templ_path = base_dir / "exporter/goldendict/templates/dpd_example.html"
        self.sbs_example_templ_path = base_dir / "exporter/goldendict/templates/sbs_example.html"
        self.inflection_templ_path = base_dir / "exporter/goldendict/templates/dpd_inflection.html"
        self.family_root_templ_path = base_dir / "exporter/goldendict/templates/dpd_family_root.html"
        self.family_word_templ_path = base_dir / "exporter/goldendict/templates/dpd_family_word.html"
        self.family_compound_templ_path = base_dir / "exporter/goldendict/templates/dpd_family_compound.html"
        self.family_idiom_templ_path = base_dir / "exporter/goldendict/templates/dpd_family_idiom.html"
        self.family_set_templ_path = base_dir / "exporter/goldendict/templates/dpd_family_set.html"
        self.frequency_templ_path = base_dir / "exporter/goldendict/templates/dpd_frequency.html"
        self.feedback_templ_path = base_dir / "exporter/goldendict/templates/dpd_feedback.html"
        self.variant_templ_path = base_dir / "exporter/goldendict/templates/dpd_variant_reading.html"
        self.spelling_templ_path = base_dir / "exporter/goldendict/templates/dpd_spelling_mistake.html"

        # FIXME delete these and whatever uses them
        # exporter/jinja templates 
        self.jinja_templates_dir = base_dir / "exporter/templates_jinja/"
        self.complete_word_templ_path = base_dir / "exporter/templates_jinja/dpd_complete_word.html"
        self.temp_html_file_path = base_dir / "temp/temp_html_file.html"


        # exporter/goldendict/templates - root
        self.root_definition_templ_path = base_dir / "exporter/goldendict/templates/root_definition.html"
        self.root_button_templ_path = base_dir / "exporter/goldendict/templates/root_buttons.html"
        self.root_info_templ_path = base_dir / "exporter/goldendict/templates/root_info.html"
        self.root_matrix_templ_path = base_dir / "exporter/goldendict/templates/root_matrix.html"
        self.root_families_templ_path = base_dir / "exporter/goldendict/templates/root_families.html"

        # exporter/goldendict/templates - other
        self.epd_templ_path = base_dir / "exporter/goldendict/templates/epd.html"
        self.deconstructor_templ_path = base_dir / "exporter/goldendict/templates/deconstructor.html"
        self.abbrev_templ_path = base_dir / "exporter/goldendict/templates/help_abbrev.html"
        self.help_templ_path = base_dir / "exporter/goldendict/templates/help_help.html"

        self.header_deconstructor_templ_path = base_dir / "exporter/goldendict/templates/header_deconstructor.html"
        self.header_grammar_dict_templ_path = base_dir / "exporter/goldendict/templates/header_grammar_dict.html"

        # exporter/tpr
        self.tpr_output_dir = base_dir / "exporter/tpr/output"
        self.tpr_sql_file_path = base_dir / "exporter/tpr/output/dpd.sql"
        self.tpr_dpd_tsv_path = base_dir / "exporter/tpr/output/dpd.tsv"
        self.tpr_i2h_tsv_path = base_dir / "exporter/tpr/output/i2h.tsv"
        self.tpr_deconstructor_tsv_path = base_dir / "exporter/tpr/output/deconstructor.tsv"

        # db/frequency/output
        self.frequency_output_dir = base_dir / "db/frequency/output/"
        self.raw_text_dir = base_dir / "db/frequency/output/raw_text/"
        self.freq_html_dir = base_dir / "db/frequency/output/html/"
        self.word_count_dir = base_dir / "db/frequency/output/word_count"
        self.tipitaka_raw_text_path = base_dir / "db/frequency/output/raw_text/tipitaka.txt"
        self.tipitaka_word_count_path = base_dir / "db/frequency/output/word_count/tipitaka.csv"
        self.ebt_raw_text_path = base_dir / "db/frequency/output/raw_text/ebts.txt"
        self.ebt_word_count_path = base_dir / "db/frequency/output/word_count/ebts.csv"

        # exporter/grammar_dict/output
        self.grammar_dict_output_dir = base_dir / "exporter/grammar_dict/output"
        self.grammar_dict_output_html_dir = base_dir / "exporter/grammar_dict/output/html"
        self.grammar_dict_pickle_path = base_dir / "exporter/grammar_dict/output/grammar_dict_pickle"
        self.grammar_dict_tsv_path = base_dir / "exporter/grammar_dict/output/grammar_dict.tsv"

        # gui
        self.pass2_checked_path = base_dir / "gui/pass2_checked.json"
        self.corrections_tsv_path = base_dir / "gui/corrections.tsv"
        self.additions_pickle_path = base_dir / "gui/additions"
        self.delated_words_history_pth = base_dir / "gui/delated_words_history.tsv"

        # gui/stash
        self.stash_dir = base_dir / "gui/stash/"
        self.stash_path = base_dir / "gui/stash/stash"
        self.save_state_path = base_dir / "gui/stash/gui_state"
        self.daily_record_path = base_dir / "gui/stash/daily_record"
        self.example_stash_path = base_dir / "gui/stash/example"

        # exporter/goldendict/icon
        self.icon_path = base_dir / "exporter/goldendict/icon//favicon.ico"
        self.icon_bmp_path = base_dir / "exporter/goldendict/icon//dpd.bmp"

        # db/inflections/
        self.inflection_templates_path = base_dir / "db/inflections/inflection_templates.xlsx"

        # exporter/other_dictionaries/css
        self.whitney_css_dir = base_dir / "exporter/other_dictionaries/code/whitney/whitney.css/"
        self.dpr_css_path = base_dir / "exporter/other_dictionaries/code/dpr/dpr.css/"

        # exporter/other_dictionaries/source
        self.bhs_source_path = base_dir / "exporter/other_dictionaries/code/bhs/source/bhs.xml"
        self.cpd_source_path = base_dir / "exporter/other_dictionaries/code/cpd/source/en-critical.json"
        self.dpr_source_path = base_dir / "exporter/other_dictionaries/code/dpr/source/dpr.json"
        self.mw_source_path = base_dir / "exporter/other_dictionaries/code/mw/source/mw_from_simsapa.json"
        self.peu_source_path = base_dir / "exporter/other_dictionaries/code/peu/source/latest.json"
        self.eng_sin_source_path = base_dir / "exporter/other_dictionaries/code/sin_eng/source/english-sinhala.tab"
        self.sin_eng_source_path = base_dir / "exporter/other_dictionaries/code/sin_eng/source/sinhala-english.tab"
        self.vri_source_path = base_dir / "exporter/other_dictionaries/code/vri/source/vri.csv"
        self.whitney_source_dir = base_dir / "exporter/other_dictionaries/code/whitney/source/"

        # exporter/other_dictionaries/goldendict
        self.bhs_gd_path = base_dir / "exporter/other_dictionaries/goldendict/bhs.zip"
        self.cpd_gd_path = base_dir / "exporter/other_dictionaries/goldendict/cpd.zip"
        self.dpr_gd_path = base_dir / "exporter/other_dictionaries/goldendict/dpr.zip"
        self.mw_gd_path = base_dir / "exporter/other_dictionaries/goldendict/mw.zip"
        self.peu_gd_path = base_dir / "exporter/other_dictionaries/goldendict/peu.zip"
        self.simsapa_gd_path = base_dir / "exporter/other_dictionaries/goldendict/simsapa.zip"
        self.sin_eng_sin_gd_path = base_dir / "exporter/other_dictionaries/goldendict/sin_eng_sin.zip"
        self.vri_gd_path = base_dir / "exporter/other_dictionaries/goldendict/vri.zip"
        self.whitney_gd_path = base_dir / "exporter/other_dictionaries/goldendict/whitney.zip"

        # exporter/other_dictionaries/json
        self.bhs_json_path = base_dir / "exporter/other_dictionaries/json/bhs.json"
        self.cpd_json_path = base_dir / "exporter/other_dictionaries/json/cpd.json"
        self.dpr_json_path = base_dir / "exporter/other_dictionaries/json/dpr.json"
        self.mw_json_path = base_dir / "exporter/other_dictionaries/json/mw.json"
        self.peu_json_path = base_dir / "exporter/other_dictionaries/json/peu.json"
        self.simsapa_json_path = base_dir / "exporter/other_dictionaries/json/simsapa.json"
        self.sin_eng_sin_json_path = base_dir / "exporter/other_dictionaries/json/sin_eng_sin.json"
        self.vri_json_path = base_dir / "exporter/other_dictionaries/json/vri.json"
        self.whitney_json_path = base_dir / "exporter/other_dictionaries/json/whitney.json"

        # exporter/other_dictionaries/mdict
        self.bhs_mdict_path = base_dir / "exporter/other_dictionaries/mdict/bhs.mdx"
        self.cpd_mdict_path = base_dir / "exporter/other_dictionaries/mdict/cpd.mdx"
        self.dpr_mdict_path = base_dir / "exporter/other_dictionaries/mdict/dpr.mdx"
        self.mw_mdict_path = base_dir / "exporter/other_dictionaries/mdict/mw.mdx"
        self.peu_mdict_path = base_dir / "exporter/other_dictionaries/mdict/peu.mdx"
        self.simsapa_mdict_path = base_dir / "exporter/other_dictionaries/mdict/simsapa.mdx"
        self.sin_eng_sin_mdict_path = base_dir / "exporter/other_dictionaries/mdict/sin_eng_sin.mdx"
        self.vri_mdict_path = base_dir / "exporter/other_dictionaries/mdict/vri.mdx"
        self.whitney_mdict_path = base_dir / "exporter/other_dictionaries/mdict/whitney.mdx"

        # resources/tipitaka-xml
        self.cst_txt_dir = base_dir / "resources/tipitaka-xml/roman_txt/"
        self.cst_xml_dir = base_dir / "resources/tipitaka-xml/deva/"
        self.cst_xml_roman_dir = base_dir / "resources/tipitaka-xml/romn/"

        # resources/resources/other_pali_texts
        self.other_pali_texts_dir = base_dir / "resources/other_pali_texts"

        # resources/sutta_central
        self.sc_dir = base_dir / "resources/sutta_central/ms/"

        # resources/tpr
        self.tpr_download_list_path = base_dir / "resources/tpr_downloads/download_source_files/download_list.json"
        self.tpr_release_path = base_dir / "resources/tpr_downloads/release_zips/dpd.zip"
        self.tpr_beta_path = base_dir / "resources/tpr_downloads/release_zips/dpd_beta.zip"

        # db/deconstructor/assets
        self.sandhi_assests_dir = base_dir / "db/deconstructor/assets"
        self.unmatched_set_path = base_dir / "db/deconstructor/assets/unmatched_set"
        self.all_inflections_set_path = base_dir / "db/deconstructor/assets/all_inflections_set"
        self.text_set_path = base_dir / "db/deconstructor/assets/text_set"
        self.neg_inflections_set_path = base_dir / "db/deconstructor/assets/neg_inflections_set"
        self.matches_dict_path = base_dir / "db/deconstructor/assets/matches_dict"

        # db/deconstructor/output
        self.sandhi_output_dir = base_dir / "db/deconstructor/output/"
        self.sandhi_output_do_dir = base_dir / "db/deconstructor/output_do/"
        self.matches_do_path = base_dir / "db/deconstructor/output_do/matches.tsv"
        self.process_path = base_dir / "db/deconstructor/output/process.tsv"
        self.matches_path = base_dir / "db/deconstructor/output/matches.tsv"
        self.unmatched_path = base_dir / "db/deconstructor/output/unmatched.tsv"
        self.matches_sorted = base_dir / "db/deconstructor/output/matches_sorted.tsv"
        self.sandhi_dict_path = base_dir / "db/deconstructor/output/sandhi_dict"
        self.sandhi_dict_df_path = base_dir / "db/deconstructor/output/sandhi_dict_df.tsv"
        self.sandhi_timer_path = base_dir / "db/deconstructor/output/timer.tsv"
        self.rule_counts_path = base_dir / "db/deconstructor/output/rule_counts/rule_counts.tsv"
        self.sandhi_log_path = base_dir / "db/deconstructor/output/logfile.log"

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

        # db/deconstructor/sandhi_related/
        self.sandhi_ok_path = base_dir / "db/deconstructor/sandhi_related/sandhi_ok.csv"
        self.sandhi_exceptions_path = base_dir / "db/deconstructor/sandhi_related/sandhi_exceptions.tsv"
        self.spelling_mistakes_path = base_dir / "db/deconstructor/sandhi_related/spelling_mistakes.tsv"
        self.variant_readings_path = base_dir / "db/deconstructor/sandhi_related/variant_readings.tsv"
        self.sandhi_rules_path = base_dir / "db/deconstructor/sandhi_related/sandhi_rules.tsv"
        self.manual_corrections_path = base_dir / "db/deconstructor/sandhi_related/manual_corrections.tsv"
        self.shortlist_path = base_dir / "db/deconstructor/sandhi_related/shortlist.tsv"

        # db/sanskrit
        self.root_families_sanskrit_path = base_dir / "db/sanskrit/root_families_sanskrit.tsv"

        # share
        self.all_tipitaka_words_path = base_dir / "share/all_tipitaka_words"
        self.template_changed_path = base_dir / "share/changed_templates"
        self.changed_headwords_path = base_dir / "share/changed_headwords"
        self.lookup_to_translit_path = base_dir / "share/lookup_to_translit.json"
        self.lookup_from_translit_path = base_dir / "share/lookup_from_translit.json"
        self.inflection_templates_pickle_path = base_dir / "share/inflection_templates"
        self.headword_stem_pattern_dict_path = base_dir / "share/headword_stem_pattern_dict"
        self.inflections_to_translit_json_path = base_dir / "share/inflections_to_translit.json"
        self.inflections_from_translit_json_path = base_dir / "share/inflections_from_translit.json"

        # resources/bw/js
        self.i2h_js_path = base_dir / "resources/bw2/js/dpd_i2h.js"
        self.dpd_ebts_js_path = base_dir / "resources/bw2/js/dpd_ebts.js"
        self.deconstructor_js_path = base_dir / "resources/bw2/js/dpd_deconstructor.js"

        # temp
        self.temp_dir = base_dir / "temp/"

        # tests/
        self.antonym_dict_path = base_dir / "tests/test_antonyms.json"
        self.bahubbihi_dict_path = base_dir / "tests/test_bahubbihis.json"
        self.compound_type_path = base_dir / "tests/add_compound_type.tsv"
        self.digu_path = base_dir / "tests/test_digu.tsv"
        self.hyphenations_dict_path = base_dir / "tests/test_hyphenations.json"
        self.hyphenations_scratchpad_path = base_dir / "tests/test_hyphenations.txt"
        self.internal_tests_path = base_dir / "tests/tests_internal.tsv"
        self.phonetic_changes_path = base_dir / "tests/add_phonetic_changes.tsv"
        self.syn_var_exceptions_old_path = base_dir / "tests/add_synonym_variant_exceptions"
        self.syn_var_exceptions_path = base_dir / "tests/add_synonym_variant.json"
        self.wf_exceptions_list = base_dir / "tests/add_word_family_exceptions"
        self.idioms_exceptions_dict = base_dir / "tests/test_idioms.json"
        self.neg_compound_exceptions = base_dir / "tests/test_neg_compound_exceptions.json"

        # tools
        self.user_dict_path = base_dir / "tools/user_dictionary.txt"

        # .. external
        self.bibliography_md_path = base_dir / "../digitalpalidictionary-website-source/src/bibliography.md"
        self.thanks_md_path = base_dir / "../digitalpalidictionary-website-source/src/thanks.md"
        self.old_roots_csv_path = base_dir / "../csvs/roots.csv"
        self.old_dpd_full_path = base_dir / "../csvs/dpd-full.csv"
        self.bjt_text_path = base_dir / "../../../../git/tipitaka.lk/public/static/text roman/"

        if create_dirs:
            self.create_dirs()

    def create_dirs(self):
        for d in [
            self.share_dir,
            self.tpr_output_dir,
            self.epub_text_dir,
            self.frequency_output_dir,
            self.grammar_dict_output_dir,
            self.grammar_dict_output_html_dir,
            self.stash_dir,
            self.cst_txt_dir,
            self.cst_xml_roman_dir,
            self.raw_text_dir,
            self.freq_html_dir,
            self.word_count_dir,
            self.temp_dir,
            self.sandhi_assests_dir,
            self.sandhi_output_dir,
            self.sandhi_output_do_dir,
            self.rule_counts_dir,
            self.letters_dir,
        ]:
            d.mkdir(parents=True, exist_ok=True)
