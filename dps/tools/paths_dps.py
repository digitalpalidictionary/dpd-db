"""All file paths that get used in the dps related codes."""

import os
from typing import Optional
from pathlib import Path

class DPSPaths:

    def __init__(self, base_dir: Optional[Path] = None, create_dirs = True):

        if base_dir is None:
            # The current working directory of the shell.
            base_dir = Path(os.path.abspath("."))

        # csvs
        self.anki_csvs_dps_dir = base_dir.joinpath(Path("dps/csvs/anki_csvs/"))
        self.csv_dps_dir = base_dir.joinpath(Path("dps/csvs/"))
        self.dpd_dps_full_path = base_dir.joinpath(Path("dps/csvs/dpd_dps_full.csv"))
        self.dps_full_path = base_dir.joinpath(Path("dps/csvs/dps_full.csv"))
        self.dps_csv_path = base_dir.joinpath(Path("dps/csvs/dps.csv"))
        self.sbs_index_path = base_dir.joinpath(Path("dps/sbs_csvs/sbs_index.csv"))
        self.class_index_path = base_dir.joinpath(Path("dps/sbs_csvs/class_index.csv"))
        self.sutta_index_path = base_dir.joinpath(Path("dps/sbs_csvs/sutta_index.csv"))
        self.freq_ebt_path = base_dir.joinpath(Path("dps/csvs/freq_ebt.csv"))
        self.dpd_dps_full_freq_path = base_dir.joinpath(Path("dps/csvs/dpd_dps_full_freq.csv"))
        self.ai_ru_suggestion_history_path = base_dir.joinpath(Path("dps/csvs/ai_ru_suggestion_history.csv"))
        self.ai_ru_notes_suggestion_history_path = base_dir.joinpath(Path("dps/csvs/ai_ru_notes_suggestion_history.csv"))
        self.ai_en_suggestion_history_path = base_dir.joinpath(Path("dps/csvs/ai_en_suggestion_history.csv"))
        self.temp_csv_path = base_dir.joinpath(Path("dps/csvs/temp.csv"))
        self.id_to_add_path = base_dir.joinpath(Path("dps/csvs/id_to_add.csv"))
        self.id_temp_list_path = base_dir.joinpath(Path("dps/csvs/id_temp_list.csv"))
        self.csvs_for_audio_dir = base_dir.joinpath(Path("dps/csvs/csvs_for_audio/"))


        self.sbs_pd_path = base_dir.joinpath(Path("dps/csvs/sbs_pd.csv"))

        # dps/exporter_ru/css_ru
        self.dpd_css_path = base_dir.joinpath(Path("dps/exporter_ru/css_ru/dpd_ru.css"))
        # self.roots_css_path = base_dir.joinpath(Path("dps/exporter_ru/css_ru/roots.css"))
        # self.deconstructor_css_path = base_dir.joinpath(Path("dps/exporter_ru/css_ru/deconstructor.css"))
        # self.help_css_path = base_dir.joinpath(Path("dps/exporter_ru/css_ru/help.css"))
        # self.grammar_css_path = base_dir.joinpath(Path("dps/exporter_ru/css_ru/grammar.css"))
        # self.variant_spelling_css_path = base_dir.joinpath(Path("dps/exporter_ru/css_ru/variant_spelling.css"))

        # /dps/exporter_ru/share
        self.share_dir = base_dir.joinpath(Path("dps/exporter_ru/share"))
        self.dpd_ru_zip_path = base_dir.joinpath(Path("dps/exporter_ru/share/ru-dpd.zip"))
        self.mdict_mdx_path = base_dir.joinpath(Path("dps/exporter_ru/share/ru-dpd-mdict.mdx"))
        # self.grammar_dict_zip_path = base_dir.joinpath(Path("dps/exporter_ru/share/dpd-grammar.zip"))
        # self.grammar_dict_mdict_path = base_dir.joinpath(Path("dps/exporter_ru/share/dpd-grammar-mdict.mdx"))
        # self.dpd_mobi_path = base_dir.joinpath(Path("dps/exporter_ru/share/dpd-kindle.mobi"))
        # self.dpd_epub_path = base_dir.joinpath(Path("dps/exporter_ru/share/dpd-kindle.epub"))
        # self.deconstructor_zip_path = base_dir.joinpath(Path("dps/exporter_ru/share/dpd-deconstructor.zip"))
        # self.deconstructor_mdict_mdx_path = base_dir.joinpath(Path("dps/exporter_ru/share/dpd-deconstructor-mdict.mdx"))
        # self.dpd_goldendict_zip_path = base_dir.joinpath(Path("dps/exporter_ru/share/dpd-goldendict.zip"))
        # self.dpd_mdict_zip_path = base_dir.joinpath(Path("dps/exporter_ru/share/dpd-mdict.zip"))

        # /dps/exporter_ru/templates_ru
        self.templates_ru_dir = base_dir.joinpath(Path("dps/exporter_ru/templates_ru"))
        self.header_templ_path = base_dir.joinpath(Path("dps/exporter_ru/templates_ru/header_ru.html"))
        self.dpd_ru_definition_templ_path = base_dir.joinpath(Path("dps/exporter_ru/templates_ru/dpd_ru_defintion.html"))
        self.button_box_templ_path = base_dir.joinpath(Path("dps/exporter_ru/templates_ru/dpd_ru_button_box.html"))
        self.grammar_templ_path = base_dir.joinpath(Path("dps/exporter_ru/templates_ru/dpd_ru_grammar.html"))
        self.example_templ_path = base_dir.joinpath(Path("dps/exporter_ru/templates_ru/dpd_ru_example.html"))
        self.inflection_templ_path = base_dir.joinpath(Path("dps/exporter_ru/templates_ru/dpd_ru_inflection.html"))
        self.family_root_templ_path = base_dir.joinpath(Path("dps/exporter_ru/templates_ru/dpd_ru_family_root.html"))
        self.family_word_templ_path = base_dir.joinpath(Path("dps/exporter_ru/templates_ru/dpd_ru_family_word.html"))
        self.family_compound_templ_path = base_dir.joinpath(Path("dps/exporter_ru/templates_ru/dpd_ru_family_compound.html"))
        self.family_idiom_templ_path = base_dir.joinpath(Path("dps/exporter_ru/templates_ru/dpd_ru_family_idiom.html"))
        self.family_set_templ_path = base_dir.joinpath(Path("dps/exporter_ru/templates_ru/dpd_ru_family_set.html"))
        self.frequency_templ_path = base_dir.joinpath(Path("dps/exporter_ru/templates_ru/dpd_ru_frequency.html"))
        self.feedback_templ_path = base_dir.joinpath(Path("dps/exporter_ru/templates_ru/dpd_ru_feedback.html"))
        self.variant_templ_path = base_dir.joinpath(Path("dps/exporter_ru/templates_ru/dpd_ru_variant_reading.html"))
        self.spelling_templ_path = base_dir.joinpath(Path("dps/exporter_ru/templates_ru/dpd_ru_spelling_mistake.html"))
        
        # # root templates_ru
        self.root_definition_templ_path = base_dir.joinpath(Path("dps/exporter_ru/templates_ru/root_definition_ru.html"))
        self.root_button_templ_path = base_dir.joinpath(Path("dps/exporter_ru/templates_ru/root_buttons_ru.html"))
        self.root_info_templ_path = base_dir.joinpath(Path("dps/exporter_ru/templates_ru/root_info_ru.html"))
        self.root_matrix_templ_path = base_dir.joinpath(Path("dps/exporter_ru/templates_ru/root_matrix_ru.html"))
        self.root_families_templ_path = base_dir.joinpath(Path("dps/exporter_ru/templates_ru/root_families_ru.html"))

        # # other templates_ru
        self.rpd_templ_path = base_dir.joinpath(Path("dps/exporter_ru/templates_ru/rpd.html"))
        # self.deconstructor_templ_path = base_dir.joinpath(Path("dps/exporter_ru/templates_ru/deconstructor.html"))
        self.abbrev_templ_path = base_dir.joinpath(Path("dps/exporter_ru/templates_ru/help_abbrev.html"))
        self.help_templ_path = base_dir.joinpath(Path("dps/exporter_ru/templates_ru/help_help.html"))

        # self.header_deconstructor_templ_path = base_dir.joinpath(Path("dps/exporter_ru/templates_ru/header_deconstructor.html"))
        # self.header_grammar_dict_templ_path = base_dir.joinpath(Path("dps/exporter_ru/templates_ru/header_grammar_dict.html"))

        # /icon
        self.icon_path = base_dir.joinpath(Path("icon/favicon.ico"))
        self.icon_bmp_path = base_dir.joinpath(Path("dps/exporter_ru/icon/book.bmp"))

        # /tests
        self.dps_internal_tests_path = base_dir.joinpath(Path("dps/csvs/dps_internal_tests.tsv"))
        self.dps_internal_tests_replaced_path = base_dir.joinpath(Path("dps/csvs/dps_internal_tests_replaced.tsv"))
        self.dps_test_1_path = base_dir.joinpath(Path("dps/csvs/dps_test_1.tsv"))
        self.dps_test_2_path = base_dir.joinpath(Path("dps/csvs/dps_test_2.tsv"))

        # spreadsheets
        self.dps_path = base_dir.joinpath(Path("dps/dps.ods"))

        # dps bakup folder
        self.dps_backup_dir = base_dir.joinpath(Path("dps/backup/")) 
        self.for_compare_dir = base_dir.joinpath(Path("dps/backup/for_compare/")) 
        self.temp_csv_backup_dir = base_dir.joinpath(Path("dps/csvs/backup_csv/")) 

        # db with frequency
        self.freq_db_path = base_dir.joinpath(Path("dps/freq.db"))

        # txt
        self.ru_user_dict_path = base_dir.joinpath(Path("dps/tools/ru_user_dictionary.txt"))
        self.text_to_add_path = base_dir.joinpath(Path("temp/text.txt"))
        self.dpd_dps_concise_txt_path = base_dir.joinpath(Path("temp/dpd_dps_concise.txt"))

        # /gui/stash
        self.dps_stash_path = base_dir.joinpath(Path("gui/stash/dps_stash.json"))
        self.dps_save_state_path = base_dir.joinpath(Path("gui/stash/dps_gui_state"))

        # .. external
        self.sbs_anki_style_dir = base_dir.joinpath(Path("../sasanarakkha/study-tools/anki-style/"))
        self.sbs_class_vocab_dir = base_dir.joinpath(Path("../sasanarakkha/study-tools/pali-class/vocab/"))
        self.local_downloads_dir = base_dir.joinpath(Path("../../Downloads/"))
        self.anki_media_dir = base_dir.joinpath(Path("/home/deva/.var/app/net.ankiweb.Anki/data/Anki2/deva/collection.media/")) 

        if create_dirs:
            self.create_dirs()


    def create_dirs(self):
            for d in [
                self.anki_csvs_dps_dir,
                self.csv_dps_dir,
                self.dps_backup_dir,
                self.for_compare_dir,
                self.temp_csv_backup_dir,
                self.csvs_for_audio_dir,
                self.templates_ru_dir,
                self.share_dir
            ]:
                d.mkdir(parents=True, exist_ok=True)

