#!/usr/bin/env python3.10

from typing import TypedDict
from pathlib import Path


class ResourcePaths(TypedDict):
    # db
    dpd_db_path: Path

    # pali texts
    cst_text_path: Path
    sc_path: Path
    bjt_text_path: Path

    # sandhi related
    sandhi_related_source_dir: Path
    sandhi_related_dest_dir: Path
    sp_mistakes_path: Path
    variant_readings_path: Path
    manual_corrections_path: Path
    exceptions: Path
    sandhi_rules_path: Path

    # assets
    unmatched_set: Path
    all_inflections_set_path: Path


def get_resource_paths() -> ResourcePaths:

    pth = ResourcePaths(
        # db
        dpd_db_path=Path("dpd.db"),

        # pali texts
        cst_text_path=Path("../Cst4/txt/"),
        sc_path=Path(
            "../Tipitaka-Pali-Projector/tipitaka_projector_data/pali/"),
        bjt_text_path=Path(
            "../../../../git/tipitaka.lk/public/static/text roman/"),

        # sandhi related
        sandhi_related_source_dir=Path(
            "../inflection generator/sandhi"),
        sandhi_related_dest_dir=Path("sandhi/sandhi_related"),
        sp_mistakes_path=Path(
            "sandhi/sandhi_related/spelling mistakes.csv"),
        variant_readings_path=Path(
            "sandhi/sandhi_related/variant readings.csv"),
        manual_corrections_path=Path(
            "sandhi/sandhi_related/manual corrections.csv"),
        shortlist_path=Path("sandhi/sandhi_related/shortlist.csv"),
        sandhi_exceptions_path=Path(
            "sandhi/sandhi_related/sandhi exceptions.csv"),
        sandhi_rules_path=Path(
            "sandhi/sandhi_related/sandhi rules.csv"),
        sandhi_css_path=Path(
            "sandhi/sandhi_related/sandhi.css"),

        # assets
        unmatched_set_path=Path(
            "sandhi/assets/unmatched_set"),
        all_inflections_set_path=Path(
            "sandhi/assets/all_inflections_set"),
        text_set_path=Path(
            "sandhi/assets/text_set"),
        neg_inflections_set_path=Path(
            "sandhi/assets/neg_inflections_set"),
        matches_dict_path=Path(
            "sandhi/assets/matches_dict"),
        matches_do_path=Path(
            "sandhi/output_do/matches.csv"),

        # output
        process_path=Path(
            "sandhi/output/process.csv"),
        matches_path=Path(
            "sandhi/output/matches.csv"),
        matches_sorted=Path(
            "sandhi/output/matches_sorted.csv"),
        sandhi_dict_path=Path(
            "sandhi/output/sandhi_dict"),
        sandhi_dict_df_path=Path(
            "sandhi/output/sandhi_dict_df.csv"),
        zip_path=Path(
            "sandhi/output/zip/padavibhāga.zip"),
        rule_counts_path=Path("sandhi/output/rule_counts/rule_counts.csv"),

        # translit
        sandhi_to_translit_path=Path("share/sandhi_to_translit.json"),
        sandhi_from_translit_path=Path("share/sandhi_from_translit.json"),

        # letters
        letters=Path("sandhi/output/letters/letters.csv"),
        letters1=Path("sandhi/output/letters/letters1.csv"),
        letters2=Path("sandhi/output/letters/letters2.csv"),
        letters3=Path("sandhi/output/letters/letters3.csv"),
        letters4=Path("sandhi/output/letters/letters4.csv"),
        letters5=Path("sandhi/output/letters/letters5.csv"),
        letters6=Path("sandhi/output/letters/letters6.csv"),
        letters7=Path("sandhi/output/letters/letters7.csv"),
        letters8=Path("sandhi/output/letters/letters8.csv"),
        letters9=Path("sandhi/output/letters/letters9.csv"),
        letters10=Path("sandhi/output/letters/letters10plus.csv"),

        # dirs
        output_dir=Path("sandhi/output/"),
        rule_counts_dir=Path("sandhi/output/rule_counts/"),
        zip_dir=Path("sandhi/output/zip/"),
        letters_dir=Path("sandhi/output/letters/")
    )

    # ensure dirs exist
    for d in [
        pth["output_dir"],
        pth["rule_counts_dir"],
        pth["zip_dir"],
        pth["letters_dir"]
    ]:
        d.mkdir(parents=True, exist_ok=True)

    return pth
