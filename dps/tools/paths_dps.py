"""All file paths that get used in the dps related codes."""

from pathlib import Path
from dataclasses import dataclass


@dataclass()
class DPSPaths():
    # csvs
    anki_csvs_dps_dir: Path = Path("dps/anki_csvs/")
    csv_dps_dir: Path = Path("dps/csvs/")
    dpd_dps_full_path: Path = Path("dps/csvs/dpd_dps_full.csv")
    dps_full_path: Path = Path("dps/csvs/dps_full.csv")
    dps_csv_path: Path = Path("dps/csvs/dps.csv")
    sbs_index_path: Path = Path("dps/csvs/sbs_index.csv")
    freq_ebt_path: Path = Path("dps/csvs/freq_ebt.csv")
    dpd_dps_full_freq_path: Path = Path("dps/csvs/dpd_dps_full_freq.csv")
    ai_suggestion_history_path: Path = Path("dps/csvs/ai_suggestion_history.csv")
    temp_csv_path: Path = Path("dps/csvs/temp.csv")
    id_to_add_path: Path = Path("dps/csvs/id_to_add.csv")

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

    # ru_user_dictionary
    ru_user_dict_path: Path = Path("dps/tools/ru_user_dictionary.txt")


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
