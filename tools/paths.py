"""All file paths that get used in the Project."""

from pathlib import Path
from dataclasses import dataclass


@dataclass()
class ProjectPaths():
    # ./ dpd_db
    dpd_db_path: Path = Path("dpd.db")

    # /anki_csvs
    anki_csvs_dir: Path = Path("anki_csvs/")
    vocab_csv_path: Path = Path("anki_csvs/vocab.csv")
    dpd_full_path: Path = Path("anki_csvs/dpd-full.csv")
    commentary_csv_path: Path = Path("anki_csvs/commentary.csv")
    pass1_csv_path: Path = Path("anki_csvs/pass1.csv")
    roots_csv_path: Path = Path("anki_csvs/roots.csv")
    family_compound_tsv_path: Path = Path("anki_csvs/family_compound.tsv")
    family_root_tsv_path: Path = Path("anki_csvs/family_root.tsv")
    family_word_tsv_path: Path = Path("anki_csvs/family_word.tsv")
    root_matrix_tsv_path: Path = Path("anki_csvs/root_matrix.tsv")

    # /backup_tsv
    pali_word_path: Path = Path("backup_tsv/paliword.tsv")
    pali_root_path: Path = Path("backup_tsv/paliroot.tsv")
    russian_path: Path = Path("backup_tsv/russian.tsv")
    sbs_path: Path = Path("backup_tsv/sbs.tsv")

    # corrections & additions
    corrections_tsv_path: Path = Path("gui/corrections.tsv")
    additions_pickle_path: Path = Path("gui/additions")

    # /definitions/
    defintions_csv_path: Path = Path(
        "definitions/definitions.csv")

    # ebook
    epub_dir: Path = Path("ebook/epub/")
    epub_dir: Path = Path("ebook/epub/")
    kindlegen_path: Path = Path("ebook/kindlegen")

    # ebook/epub
    epub_text_dir: Path = Path("ebook/epub/OEBPS/Text")
    epub_content_opf_path: Path = Path(
        "ebook/epub/OEBPS/content.opf")
    epub_abbreviations_path: Path = Path(
        "ebook/epub/OEBPS/Text/abbreviations.xhtml")
    epub_titlepage_path: Path = Path(
        "ebook/epub/OEBPS/Text/titlepage.xhtml")

    # /ebook/output
    ebook_output_dir = Path("ebook/output/")
    dpd_epub_path: Path = Path("ebook/output/dpd-kindle.epub")
    dpd_mobi_path: Path = Path("ebook/output/dpd-kindle.mobi")

    # /ebook/templates
    ebook_letter_templ_path: Path = Path(
        "ebook/templates/ebook_letter.html")
    ebook_entry_templ_path: Path = Path(
        "ebook/templates/ebook_entry.html")
    ebook_sandhi_templ_path: Path = Path(
        "ebook/templates/ebook_sandhi_entry.html")
    ebook_grammar_templ_path: Path = Path(
        "ebook/templates/ebook_grammar.html")
    ebook_example_templ_path: Path = Path(
        "ebook/templates/ebook_example.html")
    ebook_abbrev_entry_templ_path: Path = Path(
        "ebook/templates/ebook_abbreviation_entry.html")
    ebook_title_page_templ_path: Path = Path(
        "ebook/templates/ebook_titlepage.html")
    ebook_content_opf_templ_path: Path = Path(
        "ebook/templates/ebook_content_opf.html")

    # /exporter/css
    dpd_css_path: Path = Path("exporter/css/dpd.css")
    roots_css_path: Path = Path("exporter/css/roots.css")
    sandhi_css_path: Path = Path("exporter/css/sandhi.css")
    epd_css_path: Path = Path("exporter/css/epd.css")
    help_css_path: Path = Path("exporter/css/help.css")
    grammar_css_path = Path("exporter/css/grammar.css")
    variant_spelling_css_path = Path("exporter/css/variant_spelling.css")

    # /exporter/help
    abbreviations_tsv_path: Path = Path(
        "exporter/help/abbreviations.tsv")
    help_tsv_path: Path = Path("exporter/help/help.tsv")
    bibliography_tsv_path: Path = Path("exporter/help/bibliography.tsv")
    thanks_tsv_path: Path = Path("exporter/help/thanks.tsv")

    # /exporter/javascript
    buttons_js_path: Path = Path("exporter/javascript/buttons.js")

    # /exporter/share
    zip_dir: Path = Path("exporter/share")
    zip_path: Path = zip_dir/"dpd.zip"
    slob_path: Path = zip_dir/"dpd.slob"
    mdict_mdx_path: Path = zip_dir/"dpd-mdict.mdx"
    grammar_dict_zip_path: Path = zip_dir/"dpd-grammar.zip"
    grammar_dict_mdict_path: Path = zip_dir/"dpd-grammar-mdict.mdx"
    dpd_kindle_path: Path = zip_dir/"dpd-kindle.mobi"
    deconstructor_zip_path: Path = zip_dir/"dpd-deconstructor.zip"
    deconstructor_mdict_mdx_path: Path = zip_dir/"dpd-deconstructor-mdict.mdx"

    # /exporter/templates
    templates_dir: Path = Path("exporter/templates")
    header_templ_path: Path = Path("exporter/templates/header.html")
    dpd_definition_templ_path: Path = Path(
        "exporter/templates/dpd_defintion.html")
    button_box_templ_path: Path = Path(
        "exporter/templates/dpd_button_box.html")
    grammar_templ_path: Path = Path("exporter/templates/dpd_grammar.html")
    example_templ_path: Path = Path("exporter/templates/dpd_example.html")
    inflection_templ_path: Path = Path(
        "exporter/templates/dpd_inflection.html")
    family_root_templ_path: Path = Path(
        "exporter/templates/dpd_family_root.html")
    family_word_templ_path: Path = Path(
        "exporter/templates/dpd_family_word.html")
    family_compound_templ_path: Path = Path(
        "exporter/templates/dpd_family_compound.html")
    family_set_templ_path: Path = Path(
        "exporter/templates/dpd_family_set.html")
    frequency_templ_path: Path = Path(
        "exporter/templates/dpd_frequency.html")
    feedback_templ_path: Path = Path(
        "exporter/templates/dpd_feedback.html")
    variant_templ_path: Path = Path(
        "exporter/templates/dpd_variant_reading.html")
    spelling_templ_path: Path = Path(
        "exporter/templates/dpd_spelling_mistake.html")

    # # root templates
    root_definition_templ_path: Path = Path(
        "exporter/templates/root_definition.html")
    root_button_templ_path: Path = Path(
        "exporter/templates/root_buttons.html")
    root_info_templ_path: Path = Path(
        "exporter/templates/root_info.html")
    root_matrix_templ_path: Path = Path(
        "exporter/templates/root_matrix.html")
    root_families_templ_path: Path = Path(
        "exporter/templates/root_families.html")

    # # other templates
    epd_templ_path: Path = Path(
        "exporter/templates/epd.html")
    sandhi_templ_path: Path = Path(
        "exporter/templates/sandhi.html")
    abbrev_templ_path: Path = Path(
        "exporter/templates/help_abbrev.html")
    help_templ_path: Path = Path(
        "exporter/templates/help_help.html")

    header_deconstructor_templ_path: Path = Path(
        "exporter/templates/header_deconstructor.html")
    header_grammar_dict_templ_path: Path = Path(
        "exporter/templates/header_grammar_dict.html")

    # /exporter/tpr
    tpr_dir: Path = Path("exporter/tpr")
    tpr_sql_file_path: Path = Path("exporter/tpr/dpd.sql")
    tpr_dpd_tsv_path: Path = Path("exporter/tpr/dpd.tsv")
    tpr_i2h_tsv_path: Path = Path("exporter/tpr/i2h.tsv")
    tpr_deconstructor_tsv_path: Path = Path("exporter/tpr/deconstructor.tsv")

    # /frequency/output
    frequency_output_dir: Path = Path("frequency/output/")
    raw_text_dir: Path = Path("frequency/output/raw_text/")
    freq_html_dir: Path = Path("frequency/output/html/")
    word_count_dir: Path = Path(
        "frequency/output/word_count")
    tipitaka_raw_text_path: Path = Path(
        "frequency/output/raw_text/tipitaka.txt")
    tipitaka_word_count_path: Path = Path(
        "frequency/output/word_count/tipitaka.csv")
    ebt_raw_text_path: Path = Path(
        "frequency/output/raw_text/ebts.txt")
    ebt_word_count_path: Path = Path(
        "frequency/output/word_count/ebts.csv")

    # /grammar_dict/output
    grammar_dict_output_dir: Path = Path("grammar_dict/output")
    grammar_dict_output_html_dir: Path = Path("grammar_dict/output/html")
    grammar_dict_pickle_path: Path = Path(
        "grammar_dict/output/grammar_dict_pickle")
    grammar_dict_tsv_path = Path("grammar_dict/output/grammar_dict.tsv")

    # /gui/stash
    stash_dir: Path = Path("gui/stash/")
    stash_path: Path = Path("gui/stash/stash")
    save_state_path: Path = Path("gui/stash/gui_state")

    # /icon
    icon_path: Path = Path("icon/favicon.ico")
    icon_bmp_path: Path = Path("icon/dpd.bmp")

    # /inflections/
    inflection_templates_path: Path = Path(
        "inflections/inflection_templates.xlsx")

    # /resources/dpr_breakup
    dpr_breakup: Path = Path("resources/dpr_breakup/dpr_breakup.json")

    # /resources/tipitaka-xml
    cst_txt_dir: Path = Path("resources/tipitaka-xml/roman_txt/")
    cst_xml_dir: Path = Path("resources/tipitaka-xml/deva/")
    cst_xml_roman_dir: Path = Path("resources/tipitaka-xml/roman_xml/")

    # resources/resources/other_pali_texts
    other_pali_texts_dir: Path = Path("resources/other_pali_texts")

    # /resources/sutta_central
    sc_dir: Path = Path("resources/sutta_central/ms/")

    # /resources/tpr
    tpr_download_list_path: Path = Path(
        "resources/tpr_downloads/download_source_files/download_list.json")
    tpr_release_path: Path = Path(
        "resources/tpr_downloads/download_source_files/dictionaries/dpd.zip")
    tpr_beta_path: Path = Path(
        "resources/tpr_downloads/download_source_files/dictionaries/dpd_beta.zip")

    # /sandhi/assets
    sandhi_assests_dir: Path = Path("sandhi/assets")
    unmatched_set_path: Path = Path(
        "sandhi/assets/unmatched_set")
    all_inflections_set_path: Path = Path(
        "sandhi/assets/all_inflections_set")
    text_set_path: Path = Path(
        "sandhi/assets/text_set")
    neg_inflections_set_path: Path = Path(
        "sandhi/assets/neg_inflections_set")
    matches_dict_path: Path = Path(
        "sandhi/assets/matches_dict")

    # /sandhi/output
    sandhi_output_dir: Path = Path("sandhi/output/")
    sandhi_output_do_dir: Path = Path("sandhi/output_do/")
    matches_do_path: Path = Path(
        "sandhi/output_do/matches.tsv")
    process_path: Path = Path(
        "sandhi/output/process.tsv")
    matches_path: Path = Path(
        "sandhi/output/matches.tsv")
    unmatched_path: Path = Path(
        "sandhi/output/unmatched.tsv")
    matches_sorted: Path = Path(
        "sandhi/output/matches_sorted.tsv")
    sandhi_dict_path: Path = Path(
        "sandhi/output/sandhi_dict")
    sandhi_dict_df_path: Path = Path(
        "sandhi/output/sandhi_dict_df.tsv")
    sandhi_timer_path: Path = Path("sandhi/output/timer.tsv")
    rule_counts_path: Path = Path(
        "sandhi/output/rule_counts/rule_counts.tsv")

    # /sandhi/output/rule_counts
    rule_counts_dir: Path = Path("sandhi/output/rule_counts/")

    # /sandhi/output/letters
    letters_dir: Path = Path("sandhi/output/letters/")
    letters: Path = Path("sandhi/output/letters/letters.tsv")
    letters1: Path = Path("sandhi/output/letters/letters1.tsv")
    letters2: Path = Path("sandhi/output/letters/letters2.tsv")
    letters3: Path = Path("sandhi/output/letters/letters3.tsv")
    letters4: Path = Path("sandhi/output/letters/letters4.tsv")
    letters5: Path = Path("sandhi/output/letters/letters5.tsv")
    letters6: Path = Path("sandhi/output/letters/letters6.tsv")
    letters7: Path = Path("sandhi/output/letters/letters7.tsv")
    letters8: Path = Path("sandhi/output/letters/letters8.tsv")
    letters9: Path = Path("sandhi/output/letters/letters9.tsv")
    letters10: Path = Path("sandhi/output/letters/letters10plus.tsv")

    # /sandhi/sandhi_related/
    sandhi_ok_path: Path = Path("sandhi/sandhi_related/sandhi_ok.csv")
    sandhi_exceptions_path: Path = Path(
        "sandhi/sandhi_related/sandhi_exceptions.tsv")
    spelling_mistakes_path: Path = Path(
        "sandhi/sandhi_related/spelling_mistakes.tsv")
    variant_readings_path: Path = Path(
        "sandhi/sandhi_related/variant_readings.tsv")
    sandhi_rules_path: Path = Path("sandhi/sandhi_related/sandhi_rules.tsv")
    manual_corrections_path: Path = Path(
        "sandhi/sandhi_related/manual_corrections.tsv")
    shortlist_path: Path = Path("sandhi/sandhi_related/shortlist.tsv")

    # /share
    all_tipitaka_words_path: Path = Path("share/all_tipitaka_words")
    template_changed_path: Path = Path("share/changed_templates")
    changed_headwords_path: Path = Path("share/changed_headwords")
    sandhi_to_translit_path: Path = Path("share/sandhi_to_translit.json")
    sandhi_from_translit_path: Path = Path("share/sandhi_from_translit.json")
    inflection_templates_pickle_path: Path = Path("share/inflection_templates")
    headword_stem_pattern_dict_path: Path = Path(
        "share/headword_stem_pattern_dict")
    inflections_to_translit_json_path: Path = Path(
        "share/inflections_to_translit.json")
    inflections_from_translit_json_path: Path = Path(
        "share/inflections_from_translit.json")

    # /tbw
    tbw_output_dir: Path = Path("tbw/output/")
    i2h_json_path: Path = Path("tbw/output/dpd_i2h.json")
    dpd_ebts_json_path: Path = Path("tbw/output/dpd_ebts.json")
    deconstructor_json_path: Path = Path("tbw/output/dpd_deconstructor.json")

    # temp
    temp_dir: Path = Path("temp/")

    # /tests
    internal_tests_path: Path = Path("tests/internal_tests.tsv")
    wf_exceptions_list: Path = Path("tests/word_family_exceptions")
    syn_var_exceptions_path: Path = Path("tests/syn_var_exceptions")

    # tools
    user_dict_path: Path = Path("tools/user_dictionary.txt")

    # .. external
    bibliography_md_path: Path = Path(
        "../digitalpalidictionary-website-source/src/bibliography.md")
    thanks_md_path: Path = Path(
        "../digitalpalidictionary-website-source/src/thanks.md")
    old_roots_csv_path: Path = Path("../csvs/roots.csv")
    old_dpd_full_path: Path = Path("../csvs/dpd-full.csv")
    bjt_text_path: Path = Path(
        "../../../../git/tipitaka.lk/public/static/text roman/")

    @classmethod
    def create_dirs(cls):
        for d in [
            cls.anki_csvs_dir,
            cls.zip_dir,
            cls.tpr_dir,
            cls.epub_text_dir,
            cls.ebook_output_dir,
            cls.frequency_output_dir,
            cls.grammar_dict_output_dir,
            cls.grammar_dict_output_html_dir,
            cls.stash_dir,
            cls.cst_txt_dir,
            cls.cst_xml_roman_dir,
            cls.raw_text_dir,
            cls.freq_html_dir,
            cls.word_count_dir,
            cls.tbw_output_dir,
            cls.temp_dir,
            cls.sandhi_assests_dir,
            cls.sandhi_output_dir,
            cls.sandhi_output_do_dir,
            cls.rule_counts_dir,
            cls.letters_dir,
        ]:
            d.mkdir(parents=True, exist_ok=True)


# Ensure dirs exist when module is imported
ProjectPaths.create_dirs()
