from dataclasses import dataclass
from pathlib import Path


@dataclass()
class ResourcePaths():
    sandhi_ok_path: Path
    cst_texts_dir: Path
    sc_texts_dir: Path
    spelling_mistakes_path: Path
    variant_path: Path
    sandhi_rules_path: Path
    sandhi_corrections_path: Path
    spelling_corrections_path: Path
    variant_readings_path: Path
    inflection_templates_path: Path


def get_paths() -> ResourcePaths:

    pth = ResourcePaths(
        sandhi_ok_path=Path(
            "sandhi/sandhi_related/sandhi_ok.csv"),
        cst_texts_dir=Path(
            "../Cst4/txt"),
        sc_texts_dir=Path(
            "../Tipitaka-Pali-Projector/tipitaka_projector_data/pali/"),
        spelling_mistakes_path=Path(
            "sandhi/sandhi_related/spelling mistakes.csv"),
        variant_path=Path(
            "sandhi/sandhi_related/variant readings.csv"),
        sandhi_rules_path=Path(
            "sandhi/sandhi_related/sandhi rules.csv"),
        sandhi_corrections_path=Path(
            "sandhi/sandhi_related/manual corrections.csv"),
        spelling_corrections_path=Path(
            "sandhi/sandhi_related/spelling mistakes.csv"),
        variant_readings_path=Path(
            "sandhi/sandhi_related/variant readings.csv"),
        inflection_templates_path=Path(
            "inflections/inflection templates.xlsx"),
    )
    return pth
