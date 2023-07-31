"""All file paths that get used in the dps related codes."""

from pathlib import Path
from dataclasses import dataclass


@dataclass()
class DPSPaths():
    anki_csvs_dps_dir: Path = Path("dps/anki_csvs/")
    dpd_dps_full_path: Path = Path("dps/anki_csvs/dpd-dps-full.csv")
    dps_full_path: Path = Path("dps/anki_csvs/dps-full.csv")

    @classmethod
    def create_dirs(cls):
        for d in [
            cls.anki_csvs_dps_dir,
        ]:
            d.mkdir(parents=True, exist_ok=True)

# Ensure dirs exist when module is imported
DPSPaths.create_dirs()
