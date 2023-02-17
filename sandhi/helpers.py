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

    paths = ResourcePaths(
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
            "sandhi/output/padavibhāga.zip"),


    )

    # ensure write dirs exist
    # for d in [rsc['output_dir'],
    #           rsc['output_html_dir'],
    #           rsc['output_root_html_dir'],
    #           rsc['output_share_dir'],
    #           rsc['error_log_dir']]:
    #     d.mkdir(parents=True, exist_ok=True)

    return paths
