# -*- coding: utf-8 -*-
"""Compile HTML data for variants and spelling mistakes."""

import csv
from typing import List, Tuple

from mako.template import Template
from minify_html import minify

from tools.css_manager import CSSManager
from tools.goldendict_exporter import DictEntry
from tools.niggahitas import add_niggahitas
from tools.paths import ProjectPaths
from tools.printer import printer as pr
from tools.utils import (
    RenderedSizes,
    default_rendered_sizes,
    squash_whitespaces,
    sum_rendered_sizes,
)


def generate_variant_spelling_html(
    pth: ProjectPaths,
) -> Tuple[List[DictEntry], RenderedSizes]:
    """Generate html for variant readings and spelling corrections."""

    pr.green("generating variants html")

    rendered_sizes = []

    header_templ = Template(filename=str(pth.dpd_header_plain_templ_path))

    variant_dict = test_and_make_variant_dict(pth)
    spelling_dict = test_and_make_spelling_dict(pth)

    variant_data_list, sizes = generate_variant_data_list(
        pth,
        variant_dict,
        header_templ,
    )
    rendered_sizes.append(sizes)

    spelling_data_list, sizes = generate_spelling_data_list(
        pth,
        spelling_dict,
        header_templ,
    )
    rendered_sizes.append(sizes)

    if variant_data_list:
        variant_spelling_data_list = variant_data_list + spelling_data_list

    pr.yes(len(variant_spelling_data_list))
    return variant_spelling_data_list, sum_rendered_sizes(rendered_sizes)


def test_and_make_variant_dict(pth: ProjectPaths) -> dict:
    variant_dict: dict = {}

    with open(pth.variant_readings_path, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")

        for row in reader:
            variant = row["variant"]
            main = row["main"]

            # test if variant equals main reading
            if variant == main:
                pr.red(f"ERROR: variant==main! {variant}: {main}")

            # test if variant occurs twice
            if variant in variant_dict:
                pr.red(f"ERROR: dupes! {variant}")

            # all ok then add
            else:
                variant_dict[variant] = main

    return variant_dict


def generate_variant_data_list(
    pth: ProjectPaths,
    variant_dict: dict,
    header_templ: Template,
) -> Tuple[List[DictEntry], RenderedSizes]:
    size_dict = default_rendered_sizes()

    variant_templ = Template(filename=str(pth.variant_templ_path))

    header = str(header_templ.render())

    # Add Variables and fonts
    css_manager = CSSManager()
    header = css_manager.update_style(header, "primary")

    variant_data_list: List[DictEntry] = []

    for __counter__, (variant, main) in enumerate(variant_dict.items()):
        html = ""
        html += "<body>"
        html += str(variant_templ.render(main=main))
        html += "</body></html>"

        html = squash_whitespaces(header) + minify(html)

        size_dict["variant_readings"] += len(html)
        synonyms = add_niggahitas([variant])

        size_dict["variant_synonyms"] += len(str(synonyms))

        res = DictEntry(
            word=variant,
            definition_html=html,
            definition_plain="",
            synonyms=synonyms,
        )

        variant_data_list.append(res)

    return variant_data_list, size_dict


def test_and_make_spelling_dict(pth: ProjectPaths) -> dict:
    spelling_dict: dict = {}

    with open(pth.spelling_mistakes_path, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")

        for row in reader:
            mistake = row["mistake"]
            correction = row["correction"]

            # test if mistake equals correction
            if mistake == correction:
                pr.red(f"ERROR: mistake==correction! {mistake}: {correction}")

            # test if variant occurs twice
            if mistake in spelling_dict:
                pr.red(f"ERROR: dupes! {mistake}")

            # all ok then add
            else:
                spelling_dict[mistake] = correction

        assert "mātāpituraakhatañca" in spelling_dict

    return spelling_dict


def generate_spelling_data_list(
    pth: ProjectPaths,
    spelling_dict: dict,
    header_templ: Template,
) -> Tuple[List[DictEntry], RenderedSizes]:
    size_dict = default_rendered_sizes()

    spelling_templ = Template(filename=str(pth.spelling_templ_path))

    header = str(header_templ.render())

    # Add Variables and fonts
    css_manager = CSSManager()
    header = css_manager.update_style(header, "primary")

    spelling_data_list: List[DictEntry] = []

    for __counter__, (mistake, correction) in enumerate(spelling_dict.items()):
        html = ""
        html += "<body>"
        html += str(spelling_templ.render(correction=correction))
        html += "</body></html>"

        html = squash_whitespaces(header) + minify(html)

        size_dict["spelling_mistakes"] += len(html)
        synonyms = add_niggahitas([mistake])

        size_dict["spelling_synonyms"] += len(str(synonyms))

        res = DictEntry(
            word=mistake,
            definition_html=html,
            definition_plain="",
            synonyms=synonyms,
        )

        spelling_data_list.append(res)

    return spelling_data_list, size_dict


if __name__ == "__main__":
    pth = ProjectPaths()
    generate_variant_spelling_html(pth)
