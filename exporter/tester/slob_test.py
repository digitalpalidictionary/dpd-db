#!/usr/bin/env python3

"""Create a one-entry Slob smoke-test dictionary."""

from pathlib import Path

from tools.goldendict_exporter import (
    DictEntry,
    DictInfo,
    DictVariables,
    export_to_goldendict_with_pyglossary,
)
from tools.printer import printer as pr


def build_test_entry() -> DictEntry:
    definition_html = """
    <h1>DPD Slob Test</h1>
    <p>This is a one-entry smoke test for Aard2 Slob export.</p>
    <p>If this file is created in CI, the existing GoldenDict exporter path can write Slob output.</p>
    """.strip()

    return DictEntry(
        word="dpd-slob-test",
        definition_html=definition_html,
        definition_plain="DPD Slob smoke test entry.",
        synonyms=["slob-smoke-test"],
    )


def main() -> None:
    pr.tic()
    pr.yellow_title("exporting slob smoke test")

    output_dir = Path("exporter/share")
    output_dir.mkdir(parents=True, exist_ok=True)
    dict_name = "dpd-slob-test"

    dict_info = DictInfo(
        bookname="DPD Slob Test",
        author="Bodhirasa",
        description="<p>One-entry smoke test for the DPD Slob export workflow.</p>",
        website="https://digitalpalidictionary.github.io/",
        source_lang="pi",
        target_lang="en",
    )

    dict_vars = DictVariables(
        css_paths=None,
        js_paths=None,
        gd_path=output_dir,
        md_path=output_dir,
        dict_name=dict_name,
        icon_path=None,
        font_path=None,
        zip_up=False,
        delete_original=False,
    )

    export_to_goldendict_with_pyglossary(
        dict_info,
        dict_vars,
        [build_test_entry()],
        include_slob=True,
    )

    pr.toc()


if __name__ == "__main__":
    main()
