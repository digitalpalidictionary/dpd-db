"""A test dictionary for prototyping new dictionary features."""

from pathlib import Path
from tools.goldendict_exporter import DictEntry, DictInfo, DictVariables
from tools.goldendict_exporter import export_to_goldendict_with_pyglossary
from tools.printer import printer as pr


def main():
    pr.tic()
    pr.title("exporting tester")

    dict_data: list[DictEntry] = []

    html_path = Path("exporter/tester/tester.html")
    html = html_path.read_text()
    css_path = Path("exporter/tester/tester.css")
    icon_path = Path("identity/dpd-logo-dark.svg")
    font_path = Path("exporter/tester/fonts")

    dict_entry: DictEntry = DictEntry(
        word="test",
        definition_html=html,
        definition_plain="",
        synonyms=[],
    )

    dict_data.append(dict_entry)

    dict_info = DictInfo(
        bookname="Tester",
        author="tester",
        description="Tester",
        website="Tester",
        source_lang="pi",
        target_lang="en",
    )

    dict_vars = DictVariables(
        css_path=css_path,
        js_paths=None,
        gd_path=Path("exporter/tester/"),
        md_path=Path("exporter/tester/"),
        dict_name="tester",
        icon_path=icon_path,
        font_path=font_path,
        zip_up=False,
        delete_original=False,
    )

    pr.yes(len(dict_data))

    export_to_goldendict_with_pyglossary(
        dict_info, dict_vars, dict_data, zip_synonyms=False, include_slob=False
    )

    pr.toc()


if __name__ == "__main__":
    main()


# --- To include fonts ---
# 1. make a fonts_dir, and put the fonts you want to use in there "identity/fonts"
# 2. in DictVars: `font_path=fonts_dir,`
# 3. Include the fonts in CSS with @fonts rule and in the body.
