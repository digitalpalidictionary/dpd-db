#!/usr/bin/env python3.11

# sandhi paths

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
        cst_text_path=Path("resources/Cst4/txt/"),
        sc_path=Path(
            "resources/Tipitaka-Pali-Projector/tipitaka_projector_data/pali/"),
        bjt_text_path=Path(
            "../../../../git/tipitaka.lk/public/static/text roman/"),

        # sandhi related
        sandhi_related_source_dir=Path(
            "../inflection generator/sandhi"),
        sandhi_related_dest_dir=Path("sandhi/sandhi_related"),
        sp_mistakes_path=Path(
            "sandhi/sandhi_related/spelling_mistakes.tsv"),
        variant_readings_path=Path(
            "sandhi/sandhi_related/variant_readings.tsv"),
        manual_corrections_path=Path(
            "sandhi/sandhi_related/manual_corrections.tsv"),
        shortlist_path=Path("sandhi/sandhi_related/shortlist.tsv"),
        sandhi_exceptions_path=Path(
            "sandhi/sandhi_related/sandhi_exceptions.tsv"),
        sandhi_rules_path=Path(
            "sandhi/sandhi_related/sandhi_rules.tsv"),
        sandhi_css_path=Path(
            "exporter/css/sandhi.css"),

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
            "sandhi/output_do/matches.tsv"),

        # output
        process_path=Path(
            "sandhi/output/process.tsv"),
        matches_path=Path(
            "sandhi/output/matches.tsv"),
        unmatched_path=Path(
            "sandhi/output/unmatched.tsv"),
        matches_sorted=Path(
            "sandhi/output/matches_sorted.tsv"),
        sandhi_dict_path=Path(
            "sandhi/output/sandhi_dict"),
        sandhi_dict_df_path=Path(
            "sandhi/output/sandhi_dict_df.tsv"),
        zip_path=Path(
            "sandhi/output/zip/padavibhāga.zip"),
        rule_counts_path=Path(
            "sandhi/output/rule_counts/rule_counts.tsv"),

        # translit
        sandhi_to_translit_path=Path("share/sandhi_to_translit.json"),
        sandhi_from_translit_path=Path("share/sandhi_from_translit.json"),

        # letters
        letters=Path("sandhi/output/letters/letters.tsv"),
        letters1=Path("sandhi/output/letters/letters1.tsv"),
        letters2=Path("sandhi/output/letters/letters2.tsv"),
        letters3=Path("sandhi/output/letters/letters3.tsv"),
        letters4=Path("sandhi/output/letters/letters4.tsv"),
        letters5=Path("sandhi/output/letters/letters5.tsv"),
        letters6=Path("sandhi/output/letters/letters6.tsv"),
        letters7=Path("sandhi/output/letters/letters7.tsv"),
        letters8=Path("sandhi/output/letters/letters8.tsv"),
        letters9=Path("sandhi/output/letters/letters9.tsv"),
        letters10=Path("sandhi/output/letters/letters10plus.tsv"),

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
