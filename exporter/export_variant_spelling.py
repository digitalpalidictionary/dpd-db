import csv

from css_html_js_minify import css_minify
from mako.template import Template
from minify_html import minify
from rich import print

from export_dpd import render_header_tmpl

from tools.niggahitas import add_niggahitas
from tools.paths import ProjectPaths


def generate_variant_spelling_html(
        PTH: ProjectPaths, size_dict: dict) -> str:
    """Generate html for variant readings and spelling corrections."""
    print("[green]generating variants html")

    variant_dict = test_and_make_variant_dict(PTH)
    variant_data_list, size_dict = generate_variant_data_list(
        PTH, variant_dict, size_dict)
    spelling_dict = test_and_make_spelling_dict(PTH)
    spelling_data_list, size_dict = generate_spelling_data_list(
        PTH, spelling_dict, size_dict)

    variant_spelling_data_list = variant_data_list + spelling_data_list

    return variant_spelling_data_list, size_dict


def test_and_make_variant_dict(PTH: ProjectPaths) -> dict:
    variant_dict: dict = {}

    with open(
        PTH.variant_readings_path, "r",
            newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")

        for row in reader:
            variant = row["variant"]
            main = row["main"]

            # test if variant equals main reading
            if variant == main:
                print(f"[red]variant==main! {variant}: {main}")

            # test if variant occurs twice
            if variant in variant_dict:
                print(f"[red]dupes! {variant}")

            # all ok then add
            else:
                variant_dict[variant] = main

    return variant_dict


def generate_variant_data_list(
        PTH: ProjectPaths,
        variant_dict: dict,
        size_dict: dict) -> (list, dict):

    variant_templ = Template(
        filename=str(PTH.variant_templ_path))

    with open(PTH.variant_spelling_css_path) as f:
        variant_css = f.read()
    variant_css = css_minify(variant_css)

    header = render_header_tmpl(css=variant_css, js="")

    size_dict["variant_readings"] = 0
    size_dict["variant_synonyms"] = 0
    variant_data_list = []

    for counter, (variant, main) in enumerate(variant_dict.items()):

        html = header
        html += "<body>"
        html += render_variant_templ(main, variant_templ)
        html += "</body></html>"
        html = minify(html)

        size_dict["variant_readings"] += len(html)
        synonyms = add_niggahitas([variant])

        size_dict["variant_synonyms"] += len(str(synonyms))

        variant_data_list += [{
            "word": variant,
            "definition_html": html,
            "definition_plain": "",
            "synonyms": synonyms
        }]

    return variant_data_list, size_dict


def render_variant_templ(main: str, variant_templ) -> str:
    """Render html for variant readings"""
    return str(
        variant_templ.render(
            main=main))


def test_and_make_spelling_dict(PTH: ProjectPaths) -> dict:

    spelling_dict: dict = {}

    with open(
        PTH.spelling_mistakes_path, "r",
            newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")

        for row in reader:
            mistake = row["mistake"]
            correction = row["correction"]

            # test if mistake equals correction
            if mistake == correction:
                print(f"[red]mistake==correction! {mistake}: {correction}")

            # test if variant occurs twice
            if mistake in spelling_dict:
                print(f"[red]dupes! {mistake}")

            # all ok then add
            else:
                spelling_dict[mistake] = correction

        assert "mātāpituraakhatañca" in spelling_dict

    return spelling_dict


def generate_spelling_data_list(
        PTH: ProjectPaths,
        spelling_dict: dict,
        size_dict: dict) -> (list, dict):

    spelling_templ = Template(
        filename=str(PTH.spelling_templ_path))

    with open(PTH.variant_spelling_css_path) as f:
        spelling_css = f.read()
    spelling_css = css_minify(spelling_css)

    header = render_header_tmpl(css=spelling_css, js="")

    size_dict["spelling_mistakes"] = 0
    size_dict["spelling_synonyms"] = 0
    spelling_data_list = []

    for counter, (mistake, correction) in enumerate(spelling_dict.items()):

        html = header
        html += "<body>"
        html += render_spelling_templ(correction, spelling_templ)
        html += "</body></html>"
        html = minify(html)

        size_dict["spelling_mistakes"] += len(html)
        synonyms = add_niggahitas([mistake])

        size_dict["spelling_synonyms"] += len(str(synonyms))

        spelling_data_list += [{
            "word": mistake,
            "definition_html": html,
            "definition_plain": "",
            "synonyms": synonyms
        }]

    return spelling_data_list, size_dict


def render_spelling_templ(correction: str, spelling_templ) -> str:
    """Render html for spelling mistakes"""
    return str(
        spelling_templ.render(
            correction=correction))
