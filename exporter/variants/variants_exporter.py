#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Export Variants Dict to GoldenDict and MDict."""

import re

from db.db_helpers import get_db_session
from db.models import Lookup
from tools.configger import config_test
from tools.css_manager import CSSManager
from tools.goldendict_exporter import (
    DictEntry,
    DictInfo,
    DictVariables,
    export_to_goldendict_with_pyglossary,
)
from tools.mdict_exporter import export_to_mdict
from tools.niggahitas import add_niggahitas
from tools.paths import ProjectPaths
from tools.printer import printer as pr


def make_synonyms(synonyms_list: list[str], variant: str) -> list[str]:
    """Make synonyms for a word."""

    # find single words
    variant_clean = re.sub(r" \(.+", "", variant)
    words = variant_clean.split()
    if len(words) == 1:
        if variant_clean not in synonyms_list:
            synonyms_list.append(variant_clean)

    return synonyms_list


def make_synonyms_bjt(synonyms_list: list[str], variant: str) -> list[str]:
    """Make synonyms for a word in BJT text."""

    # BJT variants are in the format: "rūpādivaggo paṭhamo – machasaṃ, PTS"
    variant_clean = re.sub(r" – .+", "", variant)
    words = variant_clean.split()
    if len(words) == 1:
        if variant_clean not in synonyms_list:
            synonyms_list.append(variant_clean)

    return synonyms_list


def main():
    pr.tic()
    pr.title("exporting variants to mdict and goldendict")

    if config_test("exporter", "make_variants", "no"):
        pr.green_title("disabled in config.ini")
        pr.toc()
        return

    pr.green("setting up data")
    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)
    variants_db: list[Lookup] = (
        db_session.query(Lookup).filter(Lookup.variant != "").all()
    )
    variants_dict = {i.lookup_key: i.variants_unpack for i in variants_db}

    dict_data: list[DictEntry] = []

    with open(pth.variants_header_path) as f:
        header = f.read()

    # Add variables and fonts to header
    css_manager = CSSManager()
    header = css_manager.update_style(header, "variants")

    pr.yes("")

    pr.green("writing html")

    for word, data_tuple in variants_dict.items():
        html_list: list[str] = []
        html_list.append(header)
        html_list.append("<body>")
        html_list.append("<div class='dpd'>")
        html_list.append("<table class='variants'>")
        html_list.append(
            "<tr><th>source</th><th>book</th><th>context</th><th>variant</th></tr>"
        )
        html_list.append("<td colspan='100%'><hr></td>")

        synonyms_list: list[str] = []

        # add various niggahita to synonyms
        if "ṃ" in word or "ṁ" in word:
            synonyms_list = add_niggahitas([word])
        old_corpus = ""

        for corpus, data2 in data_tuple.items():
            if old_corpus and old_corpus != corpus:
                html_list.append("<td colspan='100%'><hr></td>")

            for book, data3 in data2.items():
                for data_tuple in data3:
                    context, variant = data_tuple
                    if corpus == "MST" or corpus == "CST":
                        synonyms_list = make_synonyms(synonyms_list, variant)
                    if corpus == "BJT":
                        synonyms_list = make_synonyms_bjt(synonyms_list, variant)

                    # add various niggahitas to synonyms
                    synonyms_list = add_niggahitas(synonyms_list)

                    html_list.append(
                        f"<tr><td>{corpus}</td><td>{book}</td><td>{context}</td><td>{variant}</td></tr>"
                    )
            html_list.append("")
            old_corpus = corpus

        html_list.append("</table>")
        html_list.append("<p class='footer'>")
        html_list.append(
            "For more information, please visit <a class='link' href='https://digitalpalidictionary.github.io/features/variants/' target='_blank'>this webpage</a>."
        )
        html_list.append("</p>")
        html_list.append("</div>")

        html_list.append("</body>")
        html_list.append("</html>")
        html: str = "\n".join(html_list)

        dict_entry = DictEntry(
            word=word,
            definition_html=html,
            definition_plain="",
            synonyms=synonyms_list,
        )
        dict_data.append(dict_entry)

    pr.yes(len(dict_data))

    dict_info = DictInfo(
        bookname="DPD Variants",
        author="Bodhirasa",
        description="Variant readings found in Myanmar, Sri Lankan, Thai and Sutta Central texts.",
        website="wwww.dpdict.net",
        source_lang="pi",
        target_lang="pi",
    )

    dict_vars = DictVariables(
        css_paths=[pth.dpd_css_and_fonts_path],
        js_paths=None,
        gd_path=pth.share_dir,
        md_path=pth.share_dir,
        dict_name="dpd-variants",
        icon_path=pth.dpd_logo_svg,
        font_path=pth.fonts_dir,
    )

    export_to_goldendict_with_pyglossary(
        dict_info,
        dict_vars,
        dict_data,
    )

    export_to_mdict(dict_info, dict_vars, dict_data)
    pr.toc()


if __name__ == "__main__":
    main()
