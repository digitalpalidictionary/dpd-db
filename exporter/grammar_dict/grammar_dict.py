#!/usr/bin/env python3

"""Compile HTML table of all grammatical possibilities of every inflected word-form."""

from mako.template import Template

from db.db_helpers import get_db_session
from db.models import Lookup

from exporter.goldendict.ru_components.tools.paths_ru import RuPaths
from exporter.goldendict.ru_components.tools.tools_for_ru_exporter import (
    ru_replace_abbreviations,
    load_abbreviations_dict
)

from tools.configger import config_test
from tools.css_manager import CSSManager
from tools.goldendict_exporter import DictInfo, DictVariables, DictEntry
from tools.goldendict_exporter import export_to_goldendict_with_pyglossary
from tools.mdict_exporter import export_to_mdict
from tools.niggahitas import add_niggahitas
from tools.paths import ProjectPaths
from tools.printer import printer as pr


class ProgData:
    def __init__(self) -> None:
        if config_test("dictionary", "make_mdict", "yes"):
            self.make_mdict = True
        else:
            self.make_mdict = False

        if config_test("exporter", "language", "en"):
            self.lang = "en"
        elif config_test("exporter", "language", "ru"):
            self.lang = "ru"
        else:
            raise ValueError("Invalid language parameter")

        self.pth = ProjectPaths()
        self.rupth = RuPaths()
        self.db_session = get_db_session(self.pth.dpd_db_path)

        # the grammar dictionaries
        self.html_dict: dict[str, str] = {} # Renamed from grammar_dict_html

        # goldendict and mdict data_list
        self.dict_data: list[DictEntry] = []

    def close_db(self):
        self.db_session.close()

    def commit_db(self):
        self.db_session.commit()


def main():
    pr.tic()
    pr.title("exporting grammar dictionary")

    if not config_test("exporter", "make_grammar", "yes"):
        pr.green("disabled in config.ini")
        pr.toc()
        return

    g = ProgData()

    generate_html_from_lookup(g) # New function replaces old ones

    g.close_db() # Close db session when done

    make_data_lists(g)
    prepare_gd_mdict_and_export(g)

    pr.toc()


def render_header_templ(
    __pth__: ProjectPaths, css: str, js: str, header_templ: Template
) -> str:
    """render the html header with css and js"""

    return str(header_templ.render(css=css, js=js))


def generate_html_from_lookup(g: ProgData):
    """Generate HTML grammar tables from Lookup table data."""
    pr.green_title("generating grammar html from lookup")

    # Query the Lookup table for entries with grammar data
    lookup_results = g.db_session.query(Lookup).filter(
        Lookup.grammar.is_not(None),
        Lookup.grammar != ""
    ).all()
    pr.white(f"found {len(lookup_results)} grammar entries in lookup table") # Changed pr.print to pr.white

    html_dict = {}

    # create the header from a template
    header_templ = Template(filename=str(g.pth.grammar_dict_header_templ_path))
    html_header = render_header_templ(g.pth, css="", js="", header_templ=header_templ)

    # Add variables and fonts to header
    css_manager = CSSManager()
    html_header = css_manager.update_style(html_header)

    html_header += "<body><div class='dpd'><table class='grammar_dict'>"
    html_header += "<thead><tr><th id='col1'>pos ⇅</th><th id='col2'>⇅</th><th id='col3'>⇅</th><th id='col4'>⇅</th><th id='col5'></th><th id='col6'>word ⇅</th></tr></thead><tbody>"

    # Process each lookup entry
    for counter, lookup_entry in enumerate(lookup_results):
        inflected_word = lookup_entry.lookup_key
        grammar_data_list = lookup_entry.grammar_unpack # [(headword, pos, grammar_str)]

        html_lines = []
        for data_tuple in grammar_data_list:
            headword, pos, grammar_str = data_tuple
            html_line = "<tr>"
            html_line += f"<td><b>{pos}</b></td>"

            # get grammatical_categories from grammar_str
            grammatical_categories = []
            if grammar_str.startswith("reflx"):
                grammatical_categories.append(
                    grammar_str.split()[0]
                    + " "
                    + grammar_str.split()[1]
                )
                grammatical_categories += grammar_str.split()[2:]
                for grammatical_category in grammatical_categories:
                    html_line += f"<td>{grammatical_category}</td>"
            elif grammar_str.startswith("in comps"):
                html_line += f"<td colspan='3'>{grammar_str}</td>"
            else:
                grammatical_categories = grammar_str.split()
                # adding empty values if there are less than 3
                while len(grammatical_categories) < 3:
                    grammatical_categories.append("")
                for grammatical_category in grammatical_categories:
                    html_line += f"<td>{grammatical_category}</td>"

            html_line += "<td>of</td>"
            html_line += f"<td>{headword}</td>"
            html_line += "</tr>"
            html_lines.append(html_line)

        # Assemble the full HTML for the entry
        entry_html = html_header + "".join(html_lines) + "</tbody></table></div></body></html>"
        html_dict[inflected_word] = entry_html

        if counter % 10000 == 0:
            pr.counter(counter, len(lookup_results), inflected_word)

    # Handle Russian translation if needed
    if g.lang == "ru":
        pr.green("replacing abbreviations: en > ru")
        print_counter = 0

        # Preload abbreviations dictionary and patterns
        load_abbreviations_dict(g.pth.abbreviations_tsv_path)

        for inflected_word, html_content in html_dict.items():
            # Split carefully to preserve the header part
            header_part, table_part = html_content.split("<tbody>", 1)
            body_part, footer_part = table_part.rsplit("</tbody>", 1)

            html_rows = body_part.split("<tr>")
            processed_rows = []
            for i, row in enumerate(html_rows):
                if row.strip():  # Skip empty strings resulting from split
                    # Add back the '<tr>' tag for processing
                    full_row = f"<tr>{row}"
                    # Replace abbreviations in the row
                    processed_row = ru_replace_abbreviations(full_row, kind="gram")
                    # Remove the added '<tr>' tag before storing
                    processed_rows.append(processed_row.replace("<tr>", "", 1))

            # Join the modified rows back
            modified_body = "<tr>".join(processed_rows)

            # Reassemble the full HTML
            html_dict[inflected_word] = f"{header_part}<tbody>{modified_body}</tbody>{footer_part}"

            print_counter += 1
            if print_counter % 10000 == 0:
                pr.counter(print_counter, len(html_dict), inflected_word)

    g.html_dict = html_dict
    pr.yes(len(g.html_dict))


def make_data_lists(g: ProgData):
    """Make the data_lists to be consumed by GoldenDict and MDict"""
    pr.green("making data lists")

    dict_data: list[DictEntry] = []
    # Use the refactored html_dict
    for word, html in g.html_dict.items():
        synonyms = add_niggahitas([word])

        dict_data += [
            DictEntry(
                word=word, definition_html=html, definition_plain="", synonyms=synonyms
            )
        ]

    g.dict_data = dict_data
    pr.yes("ok")


def prepare_gd_mdict_and_export(g: ProgData):
    """Prepare the metadata and export to goldendict & mdict."""

    if g.lang == "en":
        dict_info = DictInfo(
            bookname="DPD Grammar",
            author="Bodhirasa",
            description="<h3>DPD Grammar</h3><p>A table of all the grammatical possibilities that a particular inflected word may have. For more information please visit the <a href='https://digitalpalidictionary.github.io/features/grammardict/' target='_blank'>DPD website</a></p>",
            website="https://digitalpalidictionary.github.io/features/grammardict/",
            source_lang="pi",
            target_lang="en",
        )
        dict_name = "dpd-grammar"

    elif g.lang == "ru":
        dict_info = DictInfo(
            bookname="DPD Грамматика",
            author="Дост. Бодхираса",
            description="<h3>DPD Грамматика</h3><p>Таблица всех грамматических возможностей, которыми может обладать определенное слово в склонении или спряжении. Для получения дополнительной информации посетите <a href='https://digitalpalidictionary.github.io/rus/grammardict.html' target='_blank'>веб-сайт DPD</a>.</p>",
            website="https://digitalpalidictionary.github.io/rus/grammardict.html",
            source_lang="pi",
            target_lang="ru",
        )
        dict_name = "ru-dpd-grammar"

    dict_vars = DictVariables(
        css_paths=[g.pth.dpd_css_path],
        js_paths=[g.pth.sorter_js_path],
        gd_path=g.pth.share_dir,
        md_path=g.pth.share_dir,
        dict_name=dict_name,
        icon_path=g.pth.dpd_logo_svg,
        zip_up=False,
        delete_original=False,
    )

    export_to_goldendict_with_pyglossary(dict_info, dict_vars, g.dict_data)

    if g.make_mdict:
        export_to_mdict(dict_info, dict_vars, g.dict_data)


if __name__ == "__main__":
    main()
