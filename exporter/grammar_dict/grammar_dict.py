#!/usr/bin/env python3

"""Compile HTML table of all grammatical possibilities of every inflected word-form."""

from mako.template import Template

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


class GlobalVars:
    def __init__(self) -> None:
        if config_test("dictionary", "make_mdict", "yes"):
            self.make_mdict = True
        else:
            self.make_mdict = False

        self.pth = ProjectPaths()
        self.db_session = get_db_session(self.pth.dpd_db_path)

        # the grammar dictionaries
        self.html_dict: dict[str, str] = {}  # Renamed from grammar_dict_html

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

    g = GlobalVars()

    generate_html_from_lookup(g)  # New function replaces old ones

    g.close_db()  # Close db session when done

    make_data_lists(g)
    prepare_gd_mdict_and_export(g)

    pr.toc()


def render_header_templ(
    __pth__: ProjectPaths, css: str, js: str, header_templ: Template
) -> str:
    """render the html header with css and js"""

    return str(header_templ.render(css=css, js=js))


def generate_grammar_row_html(data_tuple: tuple[str, str, str]) -> str:
    """Generate HTML for a single row in the grammar table."""
    headword, pos, grammar_str = data_tuple
    html_line = "<tr>"
    html_line += f"<td><b>{pos}</b></td>"

    # get grammatical_categories from grammar_str
    grammatical_categories: list[str] = []
    if grammar_str.startswith("reflx"):
        parts = grammar_str.split()
        if len(parts) >= 2:
            grammatical_categories.append(parts[0] + " " + parts[1])
            grammatical_categories += parts[2:]
        else:
            grammatical_categories.append(grammar_str)

        for grammatical_category in grammatical_categories:
            html_line += f"<td>{grammatical_category}</td>"
    elif grammar_str.startswith("in comps"):
        html_line += f"<td>{grammar_str}</td>"
        html_line += "<td class='col_empty'></td>"
        html_line += "<td class='col_empty'></td>"
    else:
        grammatical_categories = grammar_str.split()
        # adding empty values if there are less than 3
        while len(grammatical_categories) < 3:
            grammatical_categories.append("")
        for grammatical_category in grammatical_categories:
            if grammatical_category == "":
                html_line += "<td class='col_empty'></td>"
            else:
                html_line += f"<td>{grammatical_category}</td>"

    html_line += "<td>of</td>"
    html_line += f"<td>{headword}</td>"
    html_line += "</tr>"
    return html_line


def generate_html_from_lookup(g: GlobalVars):
    """Generate HTML grammar tables from Lookup table data."""
    pr.green("querying database")

    # Query the Lookup table for entries with grammar data
    lookup_results = (
        g.db_session.query(Lookup)
        .filter(Lookup.grammar.is_not(None), Lookup.grammar != "")
        .all()
    )

    pr.yes(f"{len(lookup_results)}")

    pr.green("compiling html")

    html_dict = {}

    # create the header from a template
    header_templ = Template(filename=str(g.pth.grammar_dict_header_templ_path))
    html_header = render_header_templ(g.pth, css="", js="", header_templ=header_templ)

    # Add variables and fonts to header
    css_manager = CSSManager()
    html_header = css_manager.update_style(html_header, "primary")

    html_table_start = "<body><div class='dpd'><table class='grammar_dict'>"
    html_table_start += "<thead><tr><th id='col1'>pos ⇅</th><th id='col2'>⇅</th><th id='col3'>⇅</th><th id='col4'>⇅</th><th id='col5'></th><th id='col6'>word ⇅</th></tr></thead><tbody>"

    # Cache for identical grammar sets
    grammar_cache: dict[str, str] = {}

    # Process each lookup entry
    for counter, lookup_entry in enumerate(lookup_results):
        inflected_word = lookup_entry.lookup_key
        grammar_data = lookup_entry.grammar

        if grammar_data in grammar_cache:
            html_body = grammar_cache[grammar_data]
        else:
            grammar_data_list = (
                lookup_entry.grammar_unpack
            )  # [(headword, pos, grammar_str)]

            html_lines = []
            for data_tuple in grammar_data_list:
                html_lines.append(generate_grammar_row_html(data_tuple))

            html_body = "".join(html_lines)
            grammar_cache[grammar_data] = html_body

        # Assemble the full HTML for the entry
        entry_html = (
            html_header
            + html_table_start
            + html_body
            + "</tbody></table></div></body></html>"
        )
        html_dict[inflected_word] = entry_html

    g.html_dict = html_dict
    pr.yes(len(g.html_dict))


def make_data_lists(g: GlobalVars):
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


def prepare_gd_mdict_and_export(g: GlobalVars):
    """Prepare the metadata and export to goldendict & mdict."""

    dict_info = DictInfo(
        bookname="DPD Grammar",
        author="Bodhirasa",
        description="<h3>DPD Grammar</h3><p>A table of all the grammatical possibilities that a particular inflected word may have. For more information please visit the <a href='https://digitalpalidictionary.github.io/features/grammardict/' target='_blank'>DPD website</a></p>",
        website="https://digitalpalidictionary.github.io/features/grammardict/",
        source_lang="pi",
        target_lang="en",
    )
    dict_name = "dpd-grammar"

    dict_vars = DictVariables(
        css_paths=[g.pth.dpd_css_and_fonts_path],
        js_paths=[g.pth.sorter_js_path],
        gd_path=g.pth.share_dir,
        md_path=g.pth.share_dir,
        dict_name=dict_name,
        icon_path=g.pth.dpd_logo_svg,
        font_path=g.pth.fonts_dir,
        zip_up=False,
        delete_original=False,
    )

    export_to_goldendict_with_pyglossary(dict_info, dict_vars, g.dict_data)

    if g.make_mdict:
        export_to_mdict(dict_info, dict_vars, g.dict_data)


if __name__ == "__main__":
    main()
