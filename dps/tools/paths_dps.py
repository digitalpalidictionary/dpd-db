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
        self.pali_class_dir = base_dir.joinpath(Path("dps/csvs/anki_csvs/pali_class/"))
        self.pali_class_grammar_dir = base_dir.joinpath(Path("dps/csvs/anki_csvs/pali_class/grammar/"))
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
        self.ai_translated_dir = base_dir.joinpath(Path("dps/csvs/ai_translated"))
        self.freqent_words_dir = base_dir.joinpath(Path("dps/csvs/freqent_words/"))
        self.vinaya_tsv_path = base_dir.joinpath(Path("dps/sbs_csvs/vinaya.tsv"))
        self.translation_example_path = base_dir.joinpath(Path("dps/sbs_csvs/tranlslation_examples.csv"))
        self.sbs_archive = base_dir.joinpath(Path("dps/sbs_csvs/sbs_archive.tsv"))
        self.sbs_example_corrections = base_dir.joinpath(Path("dps/csvs/sbs_example_corrections.tsv"))
        self.ru_apply_path = base_dir.joinpath(Path("temp/ru_apply.csv"))

        self.ai_for_batch_api_dir = base_dir.joinpath(Path("dps/csvs/ai_for_batch_api/"))
        self.ai_from_batch_api_dir = base_dir.joinpath(Path("dps/csvs/ai_from_batch_api/"))

        self.sbs_pd_path = base_dir.joinpath(Path("dps/csvs/sbs_pd.csv"))
        self.ru_total_root_path = base_dir.joinpath(Path("dps/rus/ru_total_roots.tsv"))
        self.ru_total_comp_path = base_dir.joinpath(Path("dps/rus/ru_total_comps.tsv"))
        self.total_words_path = base_dir.joinpath(Path("dps/csvs/total_words.tsv"))
        self.total_roots_path = base_dir.joinpath(Path("dps/csvs/total_roots.tsv"))

        self.sbs_class_vocab_dir = base_dir.joinpath(Path("dps/csvs/vocab/"))

        self.pali_class_vocab_dir = base_dir.joinpath(Path("dps/pali_class/vocab/"))
        self.discourses_vocab_dir = base_dir.joinpath(Path("dps/discourses/vocab/"))

        # /tests
        self.dps_internal_tests_path = base_dir.joinpath(Path("dps/sbs_csvs/dps_internal_tests.tsv"))
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
        self.ru_user_dict_path = base_dir.joinpath(Path("dps/rus/russian_words_user_dict.txt"))
        self.text_to_add_path = base_dir.joinpath(Path("temp/text.txt"))
        self.dpd_dps_concise_txt_path = base_dir.joinpath(Path("temp/dpd_dps_concise.txt"))

        # /gui/stash
        self.dps_stash_path = base_dir.joinpath(Path("gui/stash/dps_stash.json"))
        self.dps_save_state_path = base_dir.joinpath(Path("gui/stash/dps_gui_state"))

        # .. external
        self.sbs_anki_style_dir = base_dir.joinpath(Path("../sasanarakkha/study-tools/anki-style/"))
        self.pali_class_vocab_html_dir = base_dir.joinpath(Path("../sasanarakkha/study-tools/pali-class/vocab/"))
        self.local_downloads_dir = base_dir.joinpath(Path("../../Downloads/"))
        self.anki_media_dir = base_dir.joinpath(Path("/home/deva/.var/app/net.ankiweb.Anki/data/Anki2/deva/collection.media/")) 

        if create_dirs:
            self.create_dirs()


    def create_dirs(self):
            for d in [
                self.csv_dps_dir,
                self.anki_csvs_dps_dir,
                self.pali_class_dir,
                self.pali_class_grammar_dir,
                self.dps_backup_dir,
                self.for_compare_dir,
                self.temp_csv_backup_dir,
                self.csvs_for_audio_dir,
                self.ai_for_batch_api_dir,
                self.ai_from_batch_api_dir,
                self.sbs_class_vocab_dir,
                self.ai_translated_dir
            ]:
                d.mkdir(parents=True, exist_ok=True)

