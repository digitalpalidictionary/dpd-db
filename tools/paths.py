"""All file paths that get used in the Project."""

import os
from typing import Optional
from pathlib import Path

class ProjectPaths:

    def __init__(self, base_dir: Optional[Path] = None, create_dirs = True):

        if base_dir is None:
            # The current working directory of the shell.
            base_dir = Path(os.path.abspath("."))

        # ./dpd_db
        self.dpd_db_path = base_dir.joinpath(Path("dpd.db"))

        # /anki_csvs
        self.anki_csvs_dir = base_dir.joinpath(Path("anki_csvs/"))
        self.vocab_csv_path = base_dir.joinpath(Path("anki_csvs/vocab.csv"))
        self.dpd_full_path = base_dir.joinpath(Path("anki_csvs/dpd-full.csv"))
        self.commentary_csv_path = base_dir.joinpath(Path("anki_csvs/commentary.csv"))
        self.pass1_csv_path = base_dir.joinpath(Path("anki_csvs/pass1.csv"))
        self.roots_csv_path = base_dir.joinpath(Path("anki_csvs/roots.csv"))
        self.family_compound_tsv_path = base_dir.joinpath(Path("anki_csvs/family_compound.tsv"))
        self.family_root_tsv_path = base_dir.joinpath(Path("anki_csvs/family_root.tsv"))
        self.family_word_tsv_path = base_dir.joinpath(Path("anki_csvs/family_word.tsv"))
        self.root_matrix_tsv_path = base_dir.joinpath(Path("anki_csvs/root_matrix.tsv"))

        # /backup_tsv
        self.pali_word_path = base_dir.joinpath(Path("backup_tsv/paliword.tsv"))
        self.pali_root_path = base_dir.joinpath(Path("backup_tsv/paliroot.tsv"))
        self.russian_path = base_dir.joinpath(Path("backup_tsv/russian.tsv"))
        self.sbs_path = base_dir.joinpath(Path("backup_tsv/sbs.tsv"))

        # corrections & additions
        self.corrections_tsv_path = base_dir.joinpath(Path("gui/corrections.tsv"))
        self.additions_pickle_path = base_dir.joinpath(Path("gui/additions"))

        # /definitions/
        self.defintions_csv_path = base_dir.joinpath(Path("definitions/definitions.csv"))

        # ebook
        self.epub_dir = base_dir.joinpath(Path("ebook/epub/"))
        self.epub_dir = base_dir.joinpath(Path("ebook/epub/"))
        self.kindlegen_path = base_dir.joinpath(Path("ebook/kindlegen"))

        # ebook/epub
        self.epub_text_dir = base_dir.joinpath(Path("ebook/epub/OEBPS/Text"))
        self.epub_content_opf_path = base_dir.joinpath(Path("ebook/epub/OEBPS/content.opf"))
        self.epub_abbreviations_path = base_dir.joinpath(Path("ebook/epub/OEBPS/Text/abbreviations.xhtml"))
        self.epub_titlepage_path = base_dir.joinpath(Path("ebook/epub/OEBPS/Text/titlepage.xhtml"))

        # /ebook/output
        self.ebook_output_dir = base_dir.joinpath(Path("ebook/output/"))
        self.dpd_epub_path = base_dir.joinpath(Path("ebook/output/dpd-kindle.epub"))
        self.dpd_mobi_path = base_dir.joinpath(Path("ebook/output/dpd-kindle.mobi"))

        # /ebook/templates
        self.ebook_letter_templ_path = base_dir.joinpath(Path("ebook/templates/ebook_letter.html"))
        self.ebook_entry_templ_path = base_dir.joinpath(Path("ebook/templates/ebook_entry.html"))
        self.ebook_sandhi_templ_path = base_dir.joinpath(Path("ebook/templates/ebook_sandhi_entry.html"))
        self.ebook_grammar_templ_path = base_dir.joinpath(Path("ebook/templates/ebook_grammar.html"))
        self.ebook_example_templ_path = base_dir.joinpath(Path("ebook/templates/ebook_example.html"))
        self.ebook_abbrev_entry_templ_path = base_dir.joinpath(Path("ebook/templates/ebook_abbreviation_entry.html"))
        self.ebook_title_page_templ_path = base_dir.joinpath(Path("ebook/templates/ebook_titlepage.html"))
        self.ebook_content_opf_templ_path = base_dir.joinpath(Path("ebook/templates/ebook_content_opf.html"))

        # /exporter/css
        self.dpd_css_path = base_dir.joinpath(Path("exporter/css/dpd.css"))
        self.roots_css_path = base_dir.joinpath(Path("exporter/css/roots.css"))
        self.sandhi_css_path = base_dir.joinpath(Path("exporter/css/sandhi.css"))
        self.epd_css_path = base_dir.joinpath(Path("exporter/css/epd.css"))
        self.help_css_path = base_dir.joinpath(Path("exporter/css/help.css"))
        self.grammar_css_path = base_dir.joinpath(Path("exporter/css/grammar.css"))
        self.variant_spelling_css_path = base_dir.joinpath(Path("exporter/css/variant_spelling.css"))

        # /exporter/help
        self.abbreviations_tsv_path = base_dir.joinpath(Path("exporter/help/abbreviations.tsv"))
        self.help_tsv_path = base_dir.joinpath(Path("exporter/help/help.tsv"))
        self.bibliography_tsv_path = base_dir.joinpath(Path("exporter/help/bibliography.tsv"))
        self.thanks_tsv_path = base_dir.joinpath(Path("exporter/help/thanks.tsv"))

        # /exporter/javascript
        self.buttons_js_path = base_dir.joinpath(Path("exporter/javascript/buttons.js"))

        # /exporter/share
        self.zip_dir = base_dir.joinpath(Path("exporter/share"))
        self.zip_path = base_dir.joinpath(Path("exporter/share/dpd.zip"))
        self.mdict_mdx_path = base_dir.joinpath(Path("exporter/share/dpd-mdict.mdx"))
        self.grammar_dict_zip_path = base_dir.joinpath(Path("exporter/share/dpd-grammar.zip"))
        self.grammar_dict_mdict_path = base_dir.joinpath(Path("exporter/share/dpd-grammar-mdict.mdx"))
        self.dpd_kindle_path = base_dir.joinpath(Path("exporter/share/dpd-kindle.mobi"))
        self.deconstructor_zip_path = base_dir.joinpath(Path("exporter/share/dpd-deconstructor.zip"))
        self.deconstructor_mdict_mdx_path = base_dir.joinpath(Path("exporter/share/dpd-deconstructor-mdict.mdx"))
        self.dpd_goldendict_zip_path = base_dir.joinpath(Path("exporter/share/dpd-goldendict.zip"))
        self.dpd_mdict_zip_path = base_dir.joinpath(Path("exporter/share/dpd-mdict.zip"))

        # /exporter/templates
        self.templates_dir = base_dir.joinpath(Path("exporter/templates"))
        self.header_templ_path = base_dir.joinpath(Path("exporter/templates/header.html"))
        self.dpd_definition_templ_path = base_dir.joinpath(Path("exporter/templates/dpd_defintion.html"))
        self.button_box_templ_path = base_dir.joinpath(Path("exporter/templates/dpd_button_box.html"))
        self.grammar_templ_path = base_dir.joinpath(Path("exporter/templates/dpd_grammar.html"))
        self.example_templ_path = base_dir.joinpath(Path("exporter/templates/dpd_example.html"))
        self.inflection_templ_path = base_dir.joinpath(Path("exporter/templates/dpd_inflection.html"))
        self.family_root_templ_path = base_dir.joinpath(Path("exporter/templates/dpd_family_root.html"))
        self.family_word_templ_path = base_dir.joinpath(Path("exporter/templates/dpd_family_word.html"))
        self.family_compound_templ_path = base_dir.joinpath(Path("exporter/templates/dpd_family_compound.html"))
        self.family_set_templ_path = base_dir.joinpath(Path("exporter/templates/dpd_family_set.html"))
        self.frequency_templ_path = base_dir.joinpath(Path("exporter/templates/dpd_frequency.html"))
        self.feedback_templ_path = base_dir.joinpath(Path("exporter/templates/dpd_feedback.html"))
        self.variant_templ_path = base_dir.joinpath(Path("exporter/templates/dpd_variant_reading.html"))
        self.spelling_templ_path = base_dir.joinpath(Path("exporter/templates/dpd_spelling_mistake.html"))

        # # root templates
        self.root_definition_templ_path = base_dir.joinpath(Path("exporter/templates/root_definition.html"))
        self.root_button_templ_path = base_dir.joinpath(Path("exporter/templates/root_buttons.html"))
        self.root_info_templ_path = base_dir.joinpath(Path("exporter/templates/root_info.html"))
        self.root_matrix_templ_path = base_dir.joinpath(Path("exporter/templates/root_matrix.html"))
        self.root_families_templ_path = base_dir.joinpath(Path("exporter/templates/root_families.html"))

        # # other templates
        self.epd_templ_path = base_dir.joinpath(Path("exporter/templates/epd.html"))
        self.sandhi_templ_path = base_dir.joinpath(Path("exporter/templates/sandhi.html"))
        self.abbrev_templ_path = base_dir.joinpath(Path("exporter/templates/help_abbrev.html"))
        self.help_templ_path = base_dir.joinpath(Path("exporter/templates/help_help.html"))

        self.header_deconstructor_templ_path = base_dir.joinpath(Path("exporter/templates/header_deconstructor.html"))
        self.header_grammar_dict_templ_path = base_dir.joinpath(Path("exporter/templates/header_grammar_dict.html"))

        # /exporter/tpr
        self.tpr_dir = base_dir.joinpath(Path("exporter/tpr"))
        self.tpr_sql_file_path = base_dir.joinpath(Path("exporter/tpr/dpd.sql"))
        self.tpr_dpd_tsv_path = base_dir.joinpath(Path("exporter/tpr/dpd.tsv"))
        self.tpr_i2h_tsv_path = base_dir.joinpath(Path("exporter/tpr/i2h.tsv"))
        self.tpr_deconstructor_tsv_path = base_dir.joinpath(Path("exporter/tpr/deconstructor.tsv"))

        # /frequency/output
        self.frequency_output_dir = base_dir.joinpath(Path("frequency/output/"))
        self.raw_text_dir = base_dir.joinpath(Path("frequency/output/raw_text/"))
        self.freq_html_dir = base_dir.joinpath(Path("frequency/output/html/"))
        self.word_count_dir = base_dir.joinpath(Path("frequency/output/word_count"))
        self.tipitaka_raw_text_path = base_dir.joinpath(Path("frequency/output/raw_text/tipitaka.txt"))
        self.tipitaka_word_count_path = base_dir.joinpath(Path("frequency/output/word_count/tipitaka.csv"))
        self.ebt_raw_text_path = base_dir.joinpath(Path("frequency/output/raw_text/ebts.txt"))
        self.ebt_word_count_path = base_dir.joinpath(Path("frequency/output/word_count/ebts.csv"))

        # /grammar_dict/output
        self.grammar_dict_output_dir = base_dir.joinpath(Path("grammar_dict/output"))
        self.grammar_dict_output_html_dir = base_dir.joinpath(Path("grammar_dict/output/html"))
        self.grammar_dict_pickle_path = base_dir.joinpath(Path("grammar_dict/output/grammar_dict_pickle"))
        self.grammar_dict_tsv_path = base_dir.joinpath(Path("grammar_dict/output/grammar_dict.tsv"))

        # /gui/stash
        self.stash_dir = base_dir.joinpath(Path("gui/stash/"))
        self.stash_path = base_dir.joinpath(Path("gui/stash/stash"))
        self.save_state_path = base_dir.joinpath(Path("gui/stash/gui_state"))

        # /icon
        self.icon_path = base_dir.joinpath(Path("icon/favicon.ico"))
        self.icon_bmp_path = base_dir.joinpath(Path("icon/dpd.bmp"))

        # /inflections/
        self.inflection_templates_path = base_dir.joinpath(Path("inflections/inflection_templates.xlsx"))

        # /resources/dpr_breakup
        self.dpr_breakup = base_dir.joinpath(Path("resources/dpr_breakup/dpr_breakup.json"))

        # /resources/tipitaka-xml
        self.cst_txt_dir = base_dir.joinpath(Path("resources/tipitaka-xml/roman_txt/"))
        self.cst_xml_dir = base_dir.joinpath(Path("resources/tipitaka-xml/deva/"))
        self.cst_xml_roman_dir = base_dir.joinpath(Path("resources/tipitaka-xml/romn/"))

        # resources/resources/other_pali_texts
        self.other_pali_texts_dir = base_dir.joinpath(Path("resources/other_pali_texts"))

        # /resources/sutta_central
        self.sc_dir = base_dir.joinpath(Path("resources/sutta_central/ms/"))

        # /resources/tpr
        self.tpr_download_list_path = base_dir.joinpath(Path("resources/tpr_downloads/download_source_files/download_list.json"))
        self.tpr_release_path = base_dir.joinpath(Path("resources/tpr_downloads/release_zips/dpd.zip"))
        self.tpr_beta_path = base_dir.joinpath(Path("resources/tpr_downloads/release_zips/dpd_beta.zip"))

        # /sandhi/assets
        self.sandhi_assests_dir = base_dir.joinpath(Path("sandhi/assets"))
        self.unmatched_set_path = base_dir.joinpath(Path("sandhi/assets/unmatched_set"))
        self.all_inflections_set_path = base_dir.joinpath(Path("sandhi/assets/all_inflections_set"))
        self.text_set_path = base_dir.joinpath(Path("sandhi/assets/text_set"))
        self.neg_inflections_set_path = base_dir.joinpath(Path("sandhi/assets/neg_inflections_set"))
        self.matches_dict_path = base_dir.joinpath(Path("sandhi/assets/matches_dict"))

        # /sandhi/output
        self.sandhi_output_dir = base_dir.joinpath(Path("sandhi/output/"))
        self.sandhi_output_do_dir = base_dir.joinpath(Path("sandhi/output_do/"))
        self.matches_do_path = base_dir.joinpath(Path("sandhi/output_do/matches.tsv"))
        self.process_path = base_dir.joinpath(Path("sandhi/output/process.tsv"))
        self.matches_path = base_dir.joinpath(Path("sandhi/output/matches.tsv"))
        self.unmatched_path = base_dir.joinpath(Path("sandhi/output/unmatched.tsv"))
        self.matches_sorted = base_dir.joinpath(Path("sandhi/output/matches_sorted.tsv"))
        self.sandhi_dict_path = base_dir.joinpath(Path("sandhi/output/sandhi_dict"))
        self.sandhi_dict_df_path = base_dir.joinpath(Path("sandhi/output/sandhi_dict_df.tsv"))
        self.sandhi_timer_path = base_dir.joinpath(Path("sandhi/output/timer.tsv"))
        self.rule_counts_path = base_dir.joinpath(Path("sandhi/output/rule_counts/rule_counts.tsv"))

        # /sandhi/output/rule_counts
        self.rule_counts_dir = base_dir.joinpath(Path("sandhi/output/rule_counts/"))

        # /sandhi/output/letters
        self.letters_dir = base_dir.joinpath(Path("sandhi/output/letters/"))
        self.letters = base_dir.joinpath(Path("sandhi/output/letters/letters.tsv"))
        self.letters1 = base_dir.joinpath(Path("sandhi/output/letters/letters1.tsv"))
        self.letters2 = base_dir.joinpath(Path("sandhi/output/letters/letters2.tsv"))
        self.letters3 = base_dir.joinpath(Path("sandhi/output/letters/letters3.tsv"))
        self.letters4 = base_dir.joinpath(Path("sandhi/output/letters/letters4.tsv"))
        self.letters5 = base_dir.joinpath(Path("sandhi/output/letters/letters5.tsv"))
        self.letters6 = base_dir.joinpath(Path("sandhi/output/letters/letters6.tsv"))
        self.letters7 = base_dir.joinpath(Path("sandhi/output/letters/letters7.tsv"))
        self.letters8 = base_dir.joinpath(Path("sandhi/output/letters/letters8.tsv"))
        self.letters9 = base_dir.joinpath(Path("sandhi/output/letters/letters9.tsv"))
        self.letters10 = base_dir.joinpath(Path("sandhi/output/letters/letters10plus.tsv"))

        # /sandhi/sandhi_related/
        self.sandhi_ok_path = base_dir.joinpath(Path("sandhi/sandhi_related/sandhi_ok.csv"))
        self.sandhi_exceptions_path = base_dir.joinpath(Path("sandhi/sandhi_related/sandhi_exceptions.tsv"))
        self.spelling_mistakes_path = base_dir.joinpath(Path("sandhi/sandhi_related/spelling_mistakes.tsv"))
        self.variant_readings_path = base_dir.joinpath(Path("sandhi/sandhi_related/variant_readings.tsv"))
        self.sandhi_rules_path = base_dir.joinpath(Path("sandhi/sandhi_related/sandhi_rules.tsv"))
        self.manual_corrections_path = base_dir.joinpath(Path("sandhi/sandhi_related/manual_corrections.tsv"))
        self.shortlist_path = base_dir.joinpath(Path("sandhi/sandhi_related/shortlist.tsv"))

        # /share
        self.all_tipitaka_words_path = base_dir.joinpath(Path("share/all_tipitaka_words"))
        self.template_changed_path = base_dir.joinpath(Path("share/changed_templates"))
        self.changed_headwords_path = base_dir.joinpath(Path("share/changed_headwords"))
        self.sandhi_to_translit_path = base_dir.joinpath(Path("share/sandhi_to_translit.json"))
        self.sandhi_from_translit_path = base_dir.joinpath(Path("share/sandhi_from_translit.json"))
        self.inflection_templates_pickle_path = base_dir.joinpath(Path("share/inflection_templates"))
        self.headword_stem_pattern_dict_path = base_dir.joinpath(Path("share/headword_stem_pattern_dict"))
        self.inflections_to_translit_json_path = base_dir.joinpath(Path("share/inflections_to_translit.json"))
        self.inflections_from_translit_json_path = base_dir.joinpath(Path("share/inflections_from_translit.json"))

        # /tbw
        self.tbw_output_dir = base_dir.joinpath(Path("tbw/output/"))
        self.i2h_json_path = base_dir.joinpath(Path("tbw/output/dpd_i2h.json"))
        self.dpd_ebts_json_path = base_dir.joinpath(Path("tbw/output/dpd_ebts.json"))
        self.deconstructor_json_path = base_dir.joinpath(Path("tbw/output/dpd_deconstructor.json"))

        # temp
        self.temp_dir = base_dir.joinpath(Path("temp/"))

        # /tests
        self.internal_tests_path = base_dir.joinpath(Path("tests/internal_tests.tsv"))
        self.wf_exceptions_list = base_dir.joinpath(Path("tests/word_family_exceptions"))
        self.syn_var_exceptions_path = base_dir.joinpath(Path("tests/syn_var_exceptions"))
        self.compound_type_path = base_dir.joinpath(Path("tests/compound_type.tsv"))
        self.phonetic_changes_path = base_dir.joinpath(Path("tests/phonetic_changes.tsv"))


        # tools
        self.user_dict_path = base_dir.joinpath(Path("tools/user_dictionary.txt"))

        # .. external
        self.bibliography_md_path = base_dir.joinpath(Path("../digitalpalidictionary-website-source/src/bibliography.md"))
        self.thanks_md_path = base_dir.joinpath(Path("../digitalpalidictionary-website-source/src/thanks.md"))
        self.old_roots_csv_path = base_dir.joinpath(Path("../csvs/roots.csv"))
        self.old_dpd_full_path = base_dir.joinpath(Path("../csvs/dpd-full.csv"))
        self.bjt_text_path = base_dir.joinpath(Path("../../../../git/tipitaka.lk/public/static/text roman/"))

        if create_dirs:
            self.create_dirs()

    def create_dirs(self):
        for d in [
            self.anki_csvs_dir,
            self.zip_dir,
            self.tpr_dir,
            self.epub_text_dir,
            self.ebook_output_dir,
            self.frequency_output_dir,
            self.grammar_dict_output_dir,
            self.grammar_dict_output_html_dir,
            self.stash_dir,
            self.cst_txt_dir,
            self.cst_xml_roman_dir,
            self.raw_text_dir,
            self.freq_html_dir,
            self.word_count_dir,
            self.tbw_output_dir,
            self.temp_dir,
            self.sandhi_assests_dir,
            self.sandhi_output_dir,
            self.sandhi_output_do_dir,
            self.rule_counts_dir,
            self.letters_dir,
        ]:
            d.mkdir(parents=True, exist_ok=True)

