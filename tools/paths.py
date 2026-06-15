"""All file paths that get used in the Project."""

import os
from pathlib import Path


class ProjectPaths:
    def __init__(self, base_dir: Path | None = None, create_dirs: bool = True):
        if base_dir is None:
            # The current working directory of the shell.
            base_dir = Path(os.path.abspath("."))

        # root
        self.docs_dir = base_dir / "docs"
        self.dpd_db_path = base_dir / "dpd.db"
        self.gmail_credentials_path = base_dir / "credentials.json"
        self.gmail_token_path = base_dir / "token.json"
        self.mk_docs_yaml = base_dir / "mkdocs.yaml"
        self.pyproject_path = base_dir / "pyproject.toml"
        self.temp_dir = base_dir / "temp"

        # audio
        self.dpd_audio_mp3_dir = base_dir / "audio/mp3s"

        # audio/db
        self.dpd_audio_db_path = base_dir / "audio/db/dpd_audio.db"
        self.dpd_audio_index_tsv_path = base_dir / "audio/db/dpd_audio_index.tsv"

        # audio/error_check
        self.audio_deleted_silent_files_path = (
            base_dir / "audio/error_check/deleted_silent_files.txt"
        )
        self.audio_skipped_threshold_path = (
            base_dir / "audio/error_check/skipped_threshold.txt"
        )
        self.audio_trimmed_files_path = base_dir / "audio/error_check/trimmed_files.txt"

        # audio/mp3s
        self.dpd_audio_female1_dir = base_dir / "audio/mp3s/Kannada_kn-f4_Neutral_0.85"
        self.dpd_audio_male1_dir = base_dir / "audio/mp3s/Kannada_kn-m4_Neutral_0.85"
        self.dpd_audio_male2_dir = base_dir / "audio/mp3s/Kannada_kn-m1_Neutral_0.85"

        # db/backup_tsv
        self.pali_root_path = base_dir / "db/backup_tsv/dpd_roots.tsv"
        self.pali_word_path = base_dir / "db/backup_tsv/dpd_headwords.tsv"
        self.sutta_info_tsv_path = base_dir / "db/backup_tsv/sutta_info.tsv"

        # db/bold_definitions
        self.bold_definitions_json_path = (
            base_dir / "db/bold_definitions/bold_definitions.json"
        )
        self.bold_definitions_tsv_path = (
            base_dir / "db/bold_definitions/bold_definitions.tsv"
        )

        # db/inflections
        self.inflection_templates_path = (
            base_dir / "db/inflections/inflection_templates.xlsx"
        )

        # db/sanskrit
        self.root_families_sanskrit_path = (
            base_dir / "db/sanskrit/root_families_sanskrit.tsv"
        )

        # db/suttas
        self.dv_catalogue_suttas_tsv_path = (
            base_dir / "db/suttas/dv_catalogue_suttas.tsv"
        )

        # db_tests
        self.internal_tests_path = base_dir / "db_tests/db_tests_columns.tsv"

        # db_tests/single
        self.add_phonetic_variants_exceptions_path = (
            base_dir / "db_tests/single/add_phonetic_variants.json"
        )
        self.antonym_dict_path = base_dir / "db_tests/single/test_antonyms.json"
        self.bahubbihi_dict_path = base_dir / "db_tests/single/test_bahubbihis.json"
        self.bold_example_path = base_dir / "db_tests/single/test_bold.json"
        self.digu_json_path = base_dir / "db_tests/single/test_digu.json"
        self.hyphenations_scratchpad_path = (
            base_dir / "db_tests/single/test_hyphenations.txt"
        )
        self.idioms_exceptions_dict = base_dir / "db_tests/single/test_idioms.json"
        self.maha_exceptions_list = (
            base_dir / "db_tests/single/test_maha_exceptions.json"
        )
        self.neg_compound_exceptions = (
            base_dir / "db_tests/single/test_neg_compound_exceptions.json"
        )
        self.phonetic_changes_vowels_path = (
            base_dir / "db_tests/single/add_phonetic_changes_vowels.tsv"
        )
        self.sukha_dukkha_finder_path = (
            base_dir / "db_tests/single/test_sukha_dukkha_finder.json"
        )
        self.syn_var_del_exceptions_path = (
            base_dir / "db_tests/single/add_synonym_variant_del.json"
        )
        self.syn_var_exceptions_path = (
            base_dir / "db_tests/single/add_synonym_variant.json"
        )
        self.theragatha_filler_path = (
            base_dir / "db_tests/single/test_theragatha_filler.pickle"
        )
        self.wf_exceptions_list = (
            base_dir / "db_tests/single/add_word_family_finder.pickle"
        )

        # db_tests_gui
        self.add_antonyms_sync_dict = (
            base_dir / "db_tests_gui/add_antonyms_sync_dict.json"
        )

        # docs
        self.docs_abbreviations_md_path = base_dir / "docs/abbreviations.md"
        self.docs_bibliography_md_path = base_dir / "docs/bibliography.md"
        self.docs_changelog_md_path = base_dir / "docs/changelog.md"
        self.docs_newsletters_md_path = base_dir / "docs/newsletters.md"
        self.docs_thanks_md_path = base_dir / "docs/thanks.md"

        # docs/pics
        self.docs_newsletters_pics_dir = base_dir / "docs/pics/newsletters"

        # docs/stylesheets
        self.docs_css_path = base_dir / "docs/stylesheets/extra.css"
        self.docs_css_variables_path = base_dir / "docs/stylesheets/dpd-variables.css"

        # exporter
        self.analysis_dir = base_dir / "exporter/analysis"
        self.share_dir = base_dir / "exporter/share"

        # exporter/deconstructor
        self.deconstructor_templ_path = (
            base_dir / "exporter/deconstructor/deconstructor.html"
        )

        # exporter/goldendict/javascript
        self.family_compound_json = (
            base_dir / "exporter/goldendict/javascript/family_compound_json.js"
        )
        self.family_compound_template_js = (
            base_dir / "exporter/goldendict/javascript/family_compound_template.js"
        )
        self.family_idiom_json = (
            base_dir / "exporter/goldendict/javascript/family_idiom_json.js"
        )
        self.family_idiom_template_js = (
            base_dir / "exporter/goldendict/javascript/family_idiom_template.js"
        )
        self.family_root_json = (
            base_dir / "exporter/goldendict/javascript/family_root_json.js"
        )
        self.family_root_template_js = (
            base_dir / "exporter/goldendict/javascript/family_root_template.js"
        )
        self.family_set_json = (
            base_dir / "exporter/goldendict/javascript/family_set_json.js"
        )
        self.family_set_template_js = (
            base_dir / "exporter/goldendict/javascript/family_set_template.js"
        )
        self.family_word_json = (
            base_dir / "exporter/goldendict/javascript/family_word_json.js"
        )
        self.family_word_template_js = (
            base_dir / "exporter/goldendict/javascript/family_word_template.js"
        )
        self.feedback_template_js = (
            base_dir / "exporter/goldendict/javascript/feedback_template.js"
        )
        self.frequency_template_js = (
            base_dir / "exporter/goldendict/javascript/frequency_template.js"
        )
        self.main_js_path = base_dir / "exporter/goldendict/javascript/main.js"
        self.sorter_js_path = base_dir / "exporter/goldendict/javascript/sorter.js"

        # exporter/goldendict/templates
        self.see_templ_path = base_dir / "exporter/goldendict/templates/dpd_see.jinja"

        # exporter/kindle
        self.epub_dir = base_dir / "exporter/kindle/epub"
        self.kindlegen_path = base_dir / "exporter/kindle/kindlegen"

        # exporter/kindle/epub/OEBPS
        self.epub_content_opf_path = base_dir / "exporter/kindle/epub/OEBPS/content.opf"
        self.epub_text_dir = base_dir / "exporter/kindle/epub/OEBPS/Text"

        # exporter/kindle/epub/OEBPS/Text
        self.epub_abbreviations_path = (
            base_dir / "exporter/kindle/epub/OEBPS/Text/abbreviations.xhtml"
        )
        self.epub_titlepage_path = (
            base_dir / "exporter/kindle/epub/OEBPS/Text/titlepage.xhtml"
        )

        # exporter/kobo
        self.kobo_templates_dir = base_dir / "exporter/kobo/templates"

        # exporter/kobo/templates
        self.kobo_css_path = base_dir / "exporter/kobo/templates/kobo.css"

        # exporter/pdf
        self.typst_lite_data_path = base_dir / "exporter/pdf/typst_data_lite.typ"

        # exporter/share
        self.change_log_md_path = base_dir / "exporter/share/change_log.md"
        self.dpd_anki_apkg_path = base_dir / "exporter/share/dpd-anki.apkg"
        self.dpd_deconstructor_goldendict_dir = (
            base_dir / "exporter/share/dpd-deconstructor"
        )
        self.dpd_deconstructor_goldendict_dir2 = (
            base_dir / "exporter/share/dpd-deconstructor2"
        )
        self.dpd_deconstructor_mdd_path = (
            base_dir / "exporter/share/dpd-deconstructor-mdict.mdd"
        )
        self.dpd_deconstructor_mdx_path = (
            base_dir / "exporter/share/dpd-deconstructor-mdict.mdx"
        )
        self.dpd_epub_path = base_dir / "exporter/share/dpd-kindle.epub"
        self.dpd_goldendict_dir = base_dir / "exporter/share/dpd"
        self.dpd_goldendict_zip_path = base_dir / "exporter/share/dpd-goldendict.zip"
        self.dpd_grammar_goldendict_dir = base_dir / "exporter/share/dpd-grammar"
        self.dpd_grammar_mdd_path = base_dir / "exporter/share/dpd-grammar-mdict.mdd"
        self.dpd_grammar_mdx_path = base_dir / "exporter/share/dpd-grammar-mdict.mdx"
        self.dpd_mdd_path = base_dir / "exporter/share/dpd-mdict.mdd"
        self.dpd_mdict_zip_path = base_dir / "exporter/share/dpd-mdict.zip"
        self.dpd_mdx_path = base_dir / "exporter/share/dpd-mdict.mdx"
        self.dpd_mobi_path = base_dir / "exporter/share/dpd-kindle.mobi"
        self.dpd_mobile_db_path = base_dir / "exporter/share/dpd-mobile.db"
        self.dpd_mobile_db_zip_path = base_dir / "exporter/share/dpd-mobile-db.zip"
        self.dpd_slob_zip_path = base_dir / "exporter/share/dpd-slob.zip"
        self.dpd_txt_path = base_dir / "exporter/share/dpd.txt"
        self.dpd_txt_zip_path = base_dir / "exporter/share/dpd-txt.zip"
        self.dpd_variants_goldendict_dir = base_dir / "exporter/share/dpd-variants"
        self.dpd_variants_mdd_path = base_dir / "exporter/share/dpd-variants-mdict.mdd"
        self.dpd_variants_mdx_path = base_dir / "exporter/share/dpd-variants-mdict.mdx"
        self.release_notes_md_path = base_dir / "exporter/share/release_notes.md"
        self.typst_lite_abbreviations_path = (
            base_dir / "exporter/share/abbreviations.pdf"
        )
        self.typst_lite_pdf_path = base_dir / "exporter/share/dpd.pdf"
        self.typst_lite_zip_path = base_dir / "exporter/share/dpd-pdf.zip"
        self.typst_pdf_path = base_dir / "exporter/share/dpd.pdf"

        # exporter/tpr
        self.tpr_output_dir = base_dir / "exporter/tpr/output"

        # exporter/tpr/output
        self.tpr_deconstructor_tsv_path = (
            base_dir / "exporter/tpr/output/deconstructor.tsv"
        )
        self.tpr_dpd_tsv_path = base_dir / "exporter/tpr/output/dpd.tsv"
        self.tpr_i2h_tsv_path = base_dir / "exporter/tpr/output/i2h.tsv"
        self.tpr_sql_file_path = base_dir / "exporter/tpr/output/dpd.sql"

        # exporter/variants
        self.variants_header_path = base_dir / "exporter/variants/variants_header.html"

        # exporter/webapp
        self.webapp_static_dir = base_dir / "exporter/webapp/static"
        self.webapp_templates_dir = base_dir / "exporter/webapp/templates"

        # exporter/webapp/static
        self.webapp_app_js_path = base_dir / "exporter/webapp/static/app.js"
        self.webapp_bold_definitions_js_path = (
            base_dir / "exporter/webapp/static/bold_definitions.js"
        )
        self.webapp_css_path = base_dir / "exporter/webapp/static/dpd.css"
        self.webapp_home_css_path = base_dir / "exporter/webapp/static/home.css"
        self.webapp_home_simple_css_path = (
            base_dir / "exporter/webapp/static/home_simple.css"
        )
        self.webapp_js_path = base_dir / "exporter/webapp/static/dpd.js"
        self.webapp_logo_dark_svg_path = (
            base_dir / "exporter/webapp/static/dpd-logo-dark.svg"
        )
        self.webapp_logo_svg_path = base_dir / "exporter/webapp/static/dpd-logo.svg"
        self.webapp_switch_css_path = base_dir / "exporter/webapp/static/switch.css"

        # go_modules/deconstructor
        self.go_deconstructor_output_dir = base_dir / "go_modules/deconstructor/output"

        # go_modules/deconstructor/output
        self.go_deconstructor_output_json = (
            base_dir / "go_modules/deconstructor/output/deconstructor_output.json"
        )

        # identity
        self.fonts_dir = base_dir / "identity/fonts"

        # identity/css
        self.dpd_css_and_fonts_path = base_dir / "identity/css/dpd-css-and-fonts.css"
        self.dpd_css_path = base_dir / "identity/css/dpd.css"
        self.dpd_fonts_css_path = base_dir / "identity/css/dpd-fonts.css"
        self.dpd_variables_css_path = base_dir / "identity/css/dpd-variables.css"

        # identity/logo
        self.dpd_logo_dark_bmp = base_dir / "identity/logo/dpd-logo-dark.bmp"
        self.dpd_logo_dark_svg = base_dir / "identity/logo/dpd-logo-dark.svg"
        self.dpd_logo_svg = base_dir / "identity/logo/dpd-logo.svg"

        # resources
        self.deconstructor_output_dir = base_dir / "resources/deconstructor_output"
        self.other_pali_texts_dir = base_dir / "resources/other_pali_texts"
        self.sya_dir = base_dir / "resources/syāmaraṭṭha_1927"
        self.tipitaka_translation_db_dir = (
            base_dir / "resources/tipitaka_translation_db"
        )

        # resources/bw2/js
        self.tbw_deconstructor_js_path = (
            base_dir / "resources/bw2/js/dpd_deconstructor.js"
        )
        self.tbw_dpd_ebts_js_path = base_dir / "resources/bw2/js/dpd_ebts.js"
        self.tbw_i2h_js_path = base_dir / "resources/bw2/js/dpd_i2h.js"

        # resources/deconstructor_output
        self.deconstructor_output_json = (
            base_dir / "resources/deconstructor_output/deconstructor_output.json"
        )
        self.deconstructor_output_tar_path = (
            base_dir / "resources/deconstructor_output/deconstructor_output.json.tar.gz"
        )

        # resources/dpd_submodules/bjt/public
        self.bjt_dir = base_dir / "resources/dpd_submodules/bjt/public/static"

        # resources/dpd_submodules/bjt/public/static
        self.bjt_books_dir = (
            base_dir / "resources/dpd_submodules/bjt/public/static/books"
        )
        self.bjt_roman_json_dir = (
            base_dir / "resources/dpd_submodules/bjt/public/static/roman_json"
        )
        self.bjt_roman_txt_dir = (
            base_dir / "resources/dpd_submodules/bjt/public/static/roman_txt"
        )
        self.bjt_sinhala_dir = (
            base_dir / "resources/dpd_submodules/bjt/public/static/text"
        )

        # resources/dpd_submodules/cst
        self.cst_txt_dir = base_dir / "resources/dpd_submodules/cst/romn_txt"
        self.cst_xml_dir = base_dir / "resources/dpd_submodules/cst/romn"

        # resources/fdg_dpd/assets/standalone-dpd
        self.fdg_deconstructor_js_path = (
            base_dir / "resources/fdg_dpd/assets/standalone-dpd/dpd_deconstructor.js"
        )
        self.fdg_dpd_ebts_js_path = (
            base_dir / "resources/fdg_dpd/assets/standalone-dpd/dpd_ebts.js"
        )
        self.fdg_i2h_js_path = (
            base_dir / "resources/fdg_dpd/assets/standalone-dpd/dpd_i2h.js"
        )

        # resources/other-dictionaries/build
        self.apte_gd_path = base_dir / "resources/other-dictionaries/build/goldendict"
        self.apte_mdict_path = base_dir / "resources/other-dictionaries/build/mdict"
        self.bhs_gd_path = base_dir / "resources/other-dictionaries/build/goldendict"
        self.bhs_mdict_path = base_dir / "resources/other-dictionaries/build/mdict"
        self.cone_gd_path = base_dir / "resources/other-dictionaries/build/goldendict"
        self.cone_mdict_path = base_dir / "resources/other-dictionaries/build/mdict"
        self.cpd_gd_path = base_dir / "resources/other-dictionaries/build/goldendict"
        self.cpd_mdict_path = base_dir / "resources/other-dictionaries/build/mdict"
        self.dppn_gd_path = base_dir / "resources/other-dictionaries/build/goldendict"
        self.dppn_mdict_path = base_dir / "resources/other-dictionaries/build/mdict"
        self.dpr_gd_path = base_dir / "resources/other-dictionaries/build/goldendict"
        self.dpr_mdict_path = base_dir / "resources/other-dictionaries/build/mdict"
        self.mw_gd_path = base_dir / "resources/other-dictionaries/build/goldendict"
        self.mw_mdict_path = base_dir / "resources/other-dictionaries/build/mdict"
        self.peu_gd_path = base_dir / "resources/other-dictionaries/build/goldendict"
        self.peu_mdict_path = base_dir / "resources/other-dictionaries/build/mdict"
        self.simsapa_gd_path = (
            base_dir / "resources/other-dictionaries/build/goldendict"
        )
        self.simsapa_mdict_path = base_dir / "resources/other-dictionaries/build/mdict"
        self.sin_eng_sin_gd_path = (
            base_dir / "resources/other-dictionaries/build/goldendict"
        )
        self.sin_eng_sin_mdict_path = (
            base_dir / "resources/other-dictionaries/build/mdict"
        )
        self.whitney_gd_path = (
            base_dir / "resources/other-dictionaries/build/goldendict"
        )
        self.whitney_mdict_path = base_dir / "resources/other-dictionaries/build/mdict"

        # resources/other-dictionaries/build/goldendict
        self.bhs_json_path = (
            base_dir / "resources/other-dictionaries/build/goldendict/bhs.json"
        )
        self.cone_json_path = (
            base_dir / "resources/other-dictionaries/build/goldendict/cone.json"
        )
        self.cpd_json_path = (
            base_dir / "resources/other-dictionaries/build/goldendict/cpd.json"
        )
        self.dppn_json = (
            base_dir / "resources/other-dictionaries/build/goldendict/dppn.json"
        )
        self.dpr_json_path = (
            base_dir / "resources/other-dictionaries/build/goldendict/dpr.json"
        )
        self.mw_json_path = (
            base_dir / "resources/other-dictionaries/build/goldendict/mw.json"
        )
        self.peu_json_path = (
            base_dir / "resources/other-dictionaries/build/goldendict/peu.json"
        )
        self.simsapa_json_path = (
            base_dir / "resources/other-dictionaries/build/goldendict/simsapa.json"
        )
        self.sin_eng_sin_json_path = (
            base_dir / "resources/other-dictionaries/build/goldendict/sin_eng_sin.json"
        )
        self.vri_gd_path = (
            base_dir / "resources/other-dictionaries/build/goldendict/vri.zip"
        )
        self.vri_json_path = (
            base_dir / "resources/other-dictionaries/build/goldendict/vri.json"
        )
        self.whitney_json_path = (
            base_dir / "resources/other-dictionaries/build/goldendict/whitney.json"
        )

        # resources/other-dictionaries/build/mdict
        self.vri_mdict_path = (
            base_dir / "resources/other-dictionaries/build/mdict/vri.mdx"
        )

        # resources/other-dictionaries/dictionaries/apte
        self.apte_css_path = (
            base_dir / "resources/other-dictionaries/dictionaries/apte/apte.css"
        )

        # resources/other-dictionaries/dictionaries/apte/source
        self.apte_source_json_path = (
            base_dir / "resources/other-dictionaries/dictionaries/apte/source/apte.json"
        )
        self.apte_zip_path = (
            base_dir
            / "resources/other-dictionaries/dictionaries/apte/source/ap90web1.zip"
        )

        # resources/other-dictionaries/dictionaries/apte/source/web
        self.apte_source_dir = (
            base_dir
            / "resources/other-dictionaries/dictionaries/apte/source/web/sqlite"
        )

        # resources/other-dictionaries/dictionaries/bhs/source
        self.bhs_source_path = (
            base_dir / "resources/other-dictionaries/dictionaries/bhs/source/bhs.xml"
        )

        # resources/other-dictionaries/dictionaries/cone
        self.cone_css_path = (
            base_dir / "resources/other-dictionaries/dictionaries/cone/cone.css"
        )

        # resources/other-dictionaries/dictionaries/cone/source
        self.cone_front_matter_path = (
            base_dir
            / "resources/other-dictionaries/dictionaries/cone/source/cone_front_matter.json"
        )
        self.cone_source_path = (
            base_dir
            / "resources/other-dictionaries/dictionaries/cone/source/cone_dict.json"
        )

        # resources/other-dictionaries/dictionaries/cpd
        self.cpd_css_path = (
            base_dir / "resources/other-dictionaries/dictionaries/cpd/cpd.css"
        )

        # resources/other-dictionaries/dictionaries/cpd/source
        self.cpd_source_path = (
            base_dir
            / "resources/other-dictionaries/dictionaries/cpd/source/cpd_clean.db"
        )

        # resources/other-dictionaries/dictionaries/dppn
        self.dppn_css_path = (
            base_dir / "resources/other-dictionaries/dictionaries/dppn/dppn.css"
        )

        # resources/other-dictionaries/dictionaries/dppn/source
        self.dppn_source_path = (
            base_dir / "resources/other-dictionaries/dictionaries/dppn/source/DPPN.json"
        )

        # resources/other-dictionaries/dictionaries/dpr
        self.dpr_css_path = (
            base_dir / "resources/other-dictionaries/dictionaries/dpr/dpr.css"
        )

        # resources/other-dictionaries/dictionaries/dpr/source
        self.dpr_source_path = (
            base_dir / "resources/other-dictionaries/dictionaries/dpr/source/dpr.json"
        )

        # resources/other-dictionaries/dictionaries/mw
        self.mw_css_path = (
            base_dir / "resources/other-dictionaries/dictionaries/mw/mw.css"
        )

        # resources/other-dictionaries/dictionaries/mw/source
        self.mw_source_json_path = (
            base_dir / "resources/other-dictionaries/dictionaries/mw/source/mw.json"
        )
        self.mw_zip_path = (
            base_dir / "resources/other-dictionaries/dictionaries/mw/source/mwweb1.zip"
        )

        # resources/other-dictionaries/dictionaries/mw/source/web
        self.mw_source_dir = (
            base_dir / "resources/other-dictionaries/dictionaries/mw/source/web/sqlite"
        )

        # resources/other-dictionaries/dictionaries/peu/source
        self.peu_source_path = (
            base_dir
            / "resources/other-dictionaries/dictionaries/peu/source/peu_dump.js"
        )

        # resources/other-dictionaries/dictionaries/sin_eng_sin/source
        self.eng_sin_source_path = (
            base_dir
            / "resources/other-dictionaries/dictionaries/sin_eng_sin/source/english-sinhala.tab"
        )
        self.sin_eng_source_path = (
            base_dir
            / "resources/other-dictionaries/dictionaries/sin_eng_sin/source/sinhala-english.tab"
        )

        # resources/other-dictionaries/dictionaries/vri/source
        self.vri_source_path = (
            base_dir / "resources/other-dictionaries/dictionaries/vri/source/vri.csv"
        )

        # resources/other-dictionaries/dictionaries/whitney
        self.whitney_css_path = (
            base_dir / "resources/other-dictionaries/dictionaries/whitney/whitney.css"
        )
        self.whitney_source_dir = (
            base_dir / "resources/other-dictionaries/dictionaries/whitney/source"
        )

        # resources/sc-data/dictionaries/simple/en
        self.sc_pli2en_dpd_json = (
            base_dir / "resources/sc-data/dictionaries/simple/en/pli2en_dpd.json"
        )

        # resources/sc-data/sc_bilara_data/root/pli
        self.sc_data_dir = base_dir / "resources/sc-data/sc_bilara_data/root/pli/ms"

        # resources/sc-data/sc_bilara_data/variant/pli
        self.sc_variants_dir = (
            base_dir / "resources/sc-data/sc_bilara_data/variant/pli/ms"
        )

        # resources/tipitaka_translation_db
        self.tipitaka_translation_db_path = (
            base_dir / "resources/tipitaka_translation_db/tipitaka-translation-data.db"
        )
        self.tipitaka_translation_db_tarball = (
            base_dir
            / "resources/tipitaka_translation_db/tipitaka-translation-data.db.zip"
        )

        # resources/tpr_downloads/download_source_files
        self.tpr_download_list_path = (
            base_dir
            / "resources/tpr_downloads/download_source_files/download_list.json"
        )

        # resources/tpr_downloads/release_zips
        self.tpr_beta_path = (
            base_dir / "resources/tpr_downloads/release_zips/dpd_beta.zip"
        )
        self.tpr_release_path = (
            base_dir / "resources/tpr_downloads/release_zips/dpd.zip"
        )

        # scripts/build
        self.newsletter_processed_json = (
            base_dir / "scripts/build/newsletter_processed.json"
        )

        # scripts/extractor
        self.extract_cone_tsv_path = base_dir / "scripts/extractor/extract_cone.tsv"
        self.extract_cpd_tsv_path = base_dir / "scripts/extractor/extract_cpd.tsv"

        # scripts/find
        self.most_common_missing_words_tsv_path = (
            base_dir / "scripts/find/most_common_missing_words.tsv"
        )

        # scripts/fix
        self.fix_synonym_entries_json_path = (
            base_dir / "scripts/fix/fix_synonym_entries.json"
        )

        # scripts/suttas
        self.suttas_dpd_dir = base_dir / "scripts/suttas/dpd"

        # scripts/suttas/vaggas
        self.compile_vaggas_tsv_path = (
            base_dir / "scripts/suttas/vaggas/compile_vaggas.tsv"
        )

        # shared_data
        self.additions_tsv_path = base_dir / "shared_data/additions.tsv"
        self.changed_headwords_path = base_dir / "shared_data/changed_headwords"
        self.corrections_tsv_path = base_dir / "shared_data/corrections.tsv"
        self.headword_stem_pattern_dict_path = (
            base_dir / "shared_data/headword_stem_pattern_dict"
        )
        self.inflections_from_translit_json_path = (
            base_dir / "shared_data/inflections_from_translit.json"
        )
        self.inflections_to_translit_json_path = (
            base_dir / "shared_data/inflections_to_translit.json"
        )
        self.lookup_from_translit_path = (
            base_dir / "shared_data/lookup_from_translit.json"
        )
        self.lookup_to_translit_path = base_dir / "shared_data/lookup_to_translit.json"
        self.major_change_meaning_history_pth = (
            base_dir / "shared_data/major_change_meaning_history.tsv"
        )
        self.template_changed_path = base_dir / "shared_data/changed_templates"
        self.user_dict_path = base_dir / "shared_data/user_dictionary.txt"

        # shared_data/deconstructor
        self.decon_checked = base_dir / "shared_data/deconstructor/checked.csv"
        self.decon_exceptions = base_dir / "shared_data/deconstructor/exceptions.tsv"
        self.decon_manual_corrections = (
            base_dir / "shared_data/deconstructor/manual_corrections.tsv"
        )
        self.sandhi_rules_path = base_dir / "shared_data/deconstructor/sandhi_rules.tsv"
        self.see_path = base_dir / "shared_data/deconstructor/see.tsv"
        self.spelling_mistakes_path = (
            base_dir / "shared_data/deconstructor/spelling_mistakes.tsv"
        )
        self.variant_readings_path = (
            base_dir / "shared_data/deconstructor/variant_readings.tsv"
        )

        # shared_data/frequency
        self.bjt_file_freq = base_dir / "shared_data/frequency/bjt_file_freq.json"
        self.bjt_freq_json = base_dir / "shared_data/frequency/bjt_freq.json"
        self.bjt_wordlist = base_dir / "shared_data/frequency/bjt_wordlist.json"
        self.cst_file_freq = base_dir / "shared_data/frequency/cst_file_freq.json"
        self.cst_freq_json = base_dir / "shared_data/frequency/cst_freq.json"
        self.cst_wordlist = base_dir / "shared_data/frequency/cst_wordlist.json"
        self.sc_file_freq = base_dir / "shared_data/frequency/sc_file_freq.json"
        self.sc_freq_json = base_dir / "shared_data/frequency/sc_freq.json"
        self.sc_wordlist = base_dir / "shared_data/frequency/sc_wordlist.json"
        self.sya_file_freq = base_dir / "shared_data/frequency/sya_file_freq.json"
        self.sya_freq_json = base_dir / "shared_data/frequency/sya_freq.json"
        self.sya_wordlist = base_dir / "shared_data/frequency/sya_wordlist.json"

        # shared_data/reference
        self.abbreviations_other_tsv_path = (
            base_dir / "shared_data/reference/abbreviations_other.tsv"
        )
        self.abbreviations_tsv_path = (
            base_dir / "shared_data/reference/abbreviations.tsv"
        )
        self.bibliography_tsv_path = base_dir / "shared_data/reference/bibliography.tsv"
        self.help_tsv_path = base_dir / "shared_data/reference/help.tsv"
        self.thanks_tsv_path = base_dir / "shared_data/reference/thanks.tsv"

        # temp
        self.temp_html_file_path = base_dir / "temp/temp_html_file.html"
        self.variants_json_path = base_dir / "temp/variants.json"

        # tools
        self.ai_models_json_path = base_dir / "tools/ai_models.json"
        self.compound_type_path = base_dir / "tools/compound_type_manager.tsv"
        self.cst_book_translator_tsv_path = base_dir / "tools/cst_book_translator.tsv"
        self.phonetic_changes_path = base_dir / "tools/phonetic_changes.tsv"
        self.proofreader_tsv_path = base_dir / "tools/proofreader.tsv"
        self.speech_marks_path = base_dir / "tools/speech_marks.json"
        self.tpr_codes_json_path = base_dir / "tools/tpr_codes.json"
        self.uposatha_day_ini = base_dir / "tools/uposatha_day.ini"

        # webapp template names (string constants, not paths)
        self.template_abbreviations = "abbreviations.html"
        self.template_abbreviations_other = "abbreviations_other.html"
        self.template_abbreviations_other_summary = "abbreviations_other_summary.html"
        self.template_abbreviations_summary = "abbreviations_summary.html"
        self.template_deconstructor = "deconstructor.html"
        self.template_deconstructor_summary = "deconstructor_summary.html"
        self.template_dpd_headword = "dpd_headword.html"
        self.template_dpd_summary = "dpd_summary.html"
        self.template_epd = "epd.html"
        self.template_epd_summary = "epd_summary.html"
        self.template_grammar = "grammar.html"
        self.template_grammar_summary = "grammar_summary.html"
        self.template_help = "help.html"
        self.template_help_summary = "help_summary.html"
        self.template_manual_variant = "manual_variant.html"
        self.template_manual_variant_summary = "manual_variant_summary.html"
        self.template_root = "root.html"
        self.template_root_summary = "root_summary.html"
        self.template_see = "see.html"
        self.template_see_summary = "see_summary.html"
        self.template_spelling = "spelling.html"
        self.template_spelling_summary = "spelling_summary.html"
        self.template_variant = "variant.html"
        self.template_variant_summary = "variant_summary.html"

        if create_dirs:
            self.create_dirs()

    def create_dirs(self):
        for d in [
            self.bjt_books_dir,
            self.bjt_roman_json_dir,
            self.bjt_roman_txt_dir,
            self.cst_txt_dir,
            self.epub_text_dir,
            self.go_deconstructor_output_dir,
            self.share_dir,
            self.temp_dir,
            self.tpr_output_dir,
        ]:
            d.mkdir(parents=True, exist_ok=True)
