"""All file paths that get used in the dps related codes."""

from pathlib import Path
from dataclasses import dataclass


@dataclass()
class DPSPaths():
    # csvs
    anki_csvs_dps_dir: Path = Path("dps/csvs/anki_csvs/")
    csv_dps_dir: Path = Path("dps/csvs/")
    dpd_dps_full_path: Path = Path("dps/csvs/dpd_dps_full.csv")
    dps_full_path: Path = Path("dps/csvs/dps_full.csv")
    dps_csv_path: Path = Path("dps/csvs/dps.csv")
    sbs_index_path: Path = Path("dps/sbs_index.csv")
    class_index_path: Path = Path("dps/csvs/class_index.csv")
    sutta_index_path: Path = Path("dps/csvs/sutta_index.csv")
    freq_ebt_path: Path = Path("dps/csvs/freq_ebt.csv")
    dpd_dps_full_freq_path: Path = Path("dps/csvs/dpd_dps_full_freq.csv")
    ai_ru_suggestion_history_path: Path = Path("dps/csvs/ai_ru_suggestion_history.csv")
    ai_ru_notes_suggestion_history_path: Path = Path("dps/csvs/ai_ru_notes_suggestion_history.csv")
    ai_en_suggestion_history_path: Path = Path("dps/csvs/ai_en_suggestion_history.csv")
    temp_csv_path: Path = Path("dps/csvs/temp.csv")
    id_to_add_path: Path = Path("dps/csvs/id_to_add.csv")
    word_to_add_path: Path = Path("dps/csvs/word_to_add.csv")
    new_words_path: Path = Path("dps/csvs/new_words.csv")

    sbs_pd_path: Path = Path("dps/csvs/sbs_pd.csv")

    # /tests
    dps_internal_tests_path: Path = Path("dps/csvs/dps_internal_tests.tsv")
    dps_internal_tests_replaced_path: Path = Path("dps/csvs/dps_internal_tests_replaced.tsv")
    dps_wf_exceptions_list: Path = Path("dps/csvs/dps_word_family_exceptions")
    dps_syn_var_exceptions_path: Path = Path("dps/csvs/dps_syn_var_exceptions")

    # sbs-tools related
    sbs_anki_style_dir: Path = Path("../sasanarakkha/study-tools/anki-style/")

    # local GoldenDict/
    local_goldendict_path: Path = Path("../GoldenDict/")

    # spreadsheets
    dps_path: Path = Path("dps/dps.ods")

    # to-merge/
    dps_merge_dir: Path = Path("dps/to-merge/")

    # db with frequency
    freq_db_path: Path = Path("dps/freq.db")

    # local Downloads
    local_downloads_dir: Path = Path("../../Downloads/")

    # dps bakup folder
    dps_backup_dir: Path = Path("dps/backup/") 
    backup_for_compare_dir: Path = Path("dps/backup/backup_for_compare/") 
    temp_csv_backup_dir: Path = Path("dps/csvs/backup_csv/") 

    # ru_user_dictionary
    ru_user_dict_path: Path = Path("dps/tools/ru_user_dictionary.txt")

    # local anki media path
    anki_media_dir: Path = Path("/home/deva/.var/app/net.ankiweb.Anki/data/Anki2/deva/collection.media/") 

    # local log dir
    log_dir: Path = Path("/home/deva/log/")


    # /gui/stash
    dps_stash_path: Path = Path("gui/stash/dps_stash.json")

    # text to add
    text_to_add: Path = Path("temp/text.txt")



    @classmethod
    def create_dirs(cls):
        for d in [
            cls.anki_csvs_dps_dir,
            cls.csv_dps_dir,
            cls.dps_backup_dir,
        ]:
            d.mkdir(parents=True, exist_ok=True)

# Ensure dirs exist when module is imported
DPSPaths.create_dirs()
