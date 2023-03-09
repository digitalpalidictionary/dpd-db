from dataclasses import dataclass
from pathlib import Path


@dataclass()
class ResourcePaths():
    # dirs
    cst_texts_dir: Path
    sc_texts_dir: Path
    cst_xml_dir: Path
    cst_xml_roman_dir: Path
    # paths
    sandhi_ok_path: Path
    spelling_mistakes_path: Path
    variant_path: Path
    sandhi_rules_path: Path
    sandhi_corrections_path: Path
    spelling_corrections_path: Path
    variant_readings_path: Path
    inflection_templates_path: Path
    defintions_csv_path: Path


def get_paths() -> ResourcePaths:

    pth = ResourcePaths(
        # dirs
        cst_texts_dir=Path(
            "../Cst4/txt"),
        sc_texts_dir=Path(
            "../Tipitaka-Pali-Projector/tipitaka_projector_data/pali/"),
        cst_xml_dir=Path(
            "../Cst4/Xml"),
        cst_xml_roman_dir=Path(
            "../Cst4/xml roman"),


        # paths
        sandhi_ok_path=Path(
            "sandhi/sandhi_related/sandhi_ok.csv"),
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
        defintions_csv_path=Path(
            "definitions/definitions.csv"),

    )
    return pth
