# -*- coding: utf-8 -*-
"""Compile HTML data for variants and spelling mistakes."""

import csv
from typing import List, Tuple

from minify_html import minify

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
from exporter.jinja2_env import get_jinja2_env
from exporter.goldendict.data_classes import SeeData, SpellingData, VariantData


def generate_variant_spelling_html(
    pth: ProjectPaths,
) -> Tuple[List[DictEntry], RenderedSizes]:
    """Generate html for see entries, variant readings and spelling corrections."""

    pr.green("generating variants html")

    rendered_sizes = []

    jinja_env = get_jinja2_env("exporter/goldendict/templates")

    see_dict = test_and_make_see_dict(pth)
    variant_dict = test_and_make_variant_dict(pth)
    spelling_dict = test_and_make_spelling_dict(pth)

    see_data_list, sizes = generate_see_data_list(pth, see_dict, jinja_env)
    rendered_sizes.append(sizes)

    variant_data_list, sizes = generate_variant_data_list(
        pth,
        variant_dict,
        jinja_env,
    )
    rendered_sizes.append(sizes)

    spelling_data_list, sizes = generate_spelling_data_list(
        pth,
        spelling_dict,
        jinja_env,
    )
    rendered_sizes.append(sizes)

    variant_spelling_data_list = see_data_list + variant_data_list + spelling_data_list

    pr.yes(len(variant_spelling_data_list))
    return variant_spelling_data_list, sum_rendered_sizes(rendered_sizes)


def test_and_make_see_dict(pth: ProjectPaths) -> dict:
    see_dict: dict = {}

    with open(pth.see_path, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")

        for row in reader:
            see = row["see"]
            headword = row["headword"]

            # test if see equals headword
            if see == headword:
                pr.red(f"ERROR: see==headword! {see}: {headword}")

            # test if see occurs twice
            if see in see_dict:
                pr.red(f"ERROR: dupes! {see}")

            # all ok then add
            else:
                see_dict[see] = headword

    return see_dict


def generate_see_data_list(
    pth: ProjectPaths,
    see_dict: dict,
    jinja_env,
) -> Tuple[List[DictEntry], RenderedSizes]:
    size_dict = default_rendered_sizes()

    template = jinja_env.get_template("dpd_see.jinja")

    see_data_list: List[DictEntry] = []

    for see, headword in see_dict.items():
        data = SeeData(see, headword, jinja_env)

        html_rendered = template.render(d=data)

        header = data.header
        body_start = html_rendered.find("<body>")
        body = html_rendered[body_start:]

        final_html = squash_whitespaces(header) + minify(body)

        size_dict["see_entries"] += len(final_html)
        synonyms = add_niggahitas([see])

        res = DictEntry(
            word=see,
            definition_html=final_html,
            definition_plain="",
            synonyms=synonyms,
        )

        see_data_list.append(res)

    return see_data_list, size_dict


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
    jinja_env,
) -> Tuple[List[DictEntry], RenderedSizes]:
    size_dict = default_rendered_sizes()

    template = jinja_env.get_template("dpd_variant_reading.jinja")

    variant_data_list: List[DictEntry] = []

    for variant, main in variant_dict.items():
        # Use ViewModel
        data = VariantData(variant, main, jinja_env)

        html_rendered = template.render(d=data)

        # Re-calculate parts for parity
        header = data.header
        body_start = html_rendered.find("<body>")
        body = html_rendered[body_start:]

        final_html = squash_whitespaces(header) + minify(body)

        size_dict["variant_readings"] += len(final_html)
        synonyms = add_niggahitas([variant])

        size_dict["variant_synonyms"] += len(str(synonyms))

        res = DictEntry(
            word=variant,
            definition_html=final_html,
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

    return spelling_dict


def generate_spelling_data_list(
    pth: ProjectPaths,
    spelling_dict: dict,
    jinja_env,
) -> Tuple[List[DictEntry], RenderedSizes]:
    size_dict = default_rendered_sizes()

    template = jinja_env.get_template("dpd_spelling_mistake.jinja")

    spelling_data_list: List[DictEntry] = []

    for mistake, correction in spelling_dict.items():
        # Use ViewModel
        data = SpellingData(mistake, correction, jinja_env)

        html_rendered = template.render(d=data)

        # Re-calculate parts for parity
        header = data.header
        body_start = html_rendered.find("<body>")
        body = html_rendered[body_start:]

        final_html = squash_whitespaces(header) + minify(body)

        size_dict["spelling_mistakes"] += len(final_html)
        synonyms = add_niggahitas([mistake])

        size_dict["spelling_synonyms"] += len(str(synonyms))

        res = DictEntry(
            word=mistake,
            definition_html=final_html,
            definition_plain="",
            synonyms=synonyms,
        )

        spelling_data_list.append(res)

    return spelling_data_list, size_dict
