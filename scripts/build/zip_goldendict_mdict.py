#!/usr/bin/env python3

"""Rezip the three files DPD into one:
1. dpd.zip, 2. dpd-grammar.zip, 3. dpd-deconstructor.zip
1. dpd.mdx .mdd, 2. dpd-grammar.mdx .mdd, 3. dpd-deconstructor.mdx .mdd"""

import os
from zipfile import ZipFile, ZIP_DEFLATED
from tools.paths import ProjectPaths
from tools.printer import printer as pr


def zip_goldendict(pth: ProjectPaths):
    """Zip up the three dirs for goldendict"""
    pr.green("zipping goldendict")

    if (
        pth.dpd_goldendict_dir.exists()
        and pth.dpd_grammar_goldendict_dir.exists()
        and pth.dpd_deconstructor_goldendict_dir.exists()
    ):
        input_dirs = [
            (pth.dpd_goldendict_dir, "dpd"),
            (pth.dpd_grammar_goldendict_dir, "dpd-grammar"),
            (pth.dpd_deconstructor_goldendict_dir, "dpd-deconstructor"),
            (pth.dpd_variants_goldendict_dir, "dpd-variants"),
        ]

        output_zip_file = pth.dpd_goldendict_zip_path

        with ZipFile(
            output_zip_file, "w", compression=ZIP_DEFLATED, compresslevel=5
        ) as output_zip:
            for input_dir, dir_name in input_dirs:
                for root, dirs, files in os.walk(input_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        # Calculate the relative path from the root of the input directory
                        relative_path = os.path.relpath(file_path, input_dir)
                        # Prepend the directory name to the relative path
                        archive_name = os.path.join(dir_name, relative_path)
                        output_zip.write(file_path, archive_name)

        pr.yes("ok")
    else:
        pr.no("error")
        pr.red("no dpd dir file found")


def zip_mdict(pth: ProjectPaths):
    """Zipping up MDict files for sharing."""

    pr.green("zipping mdict")

    mdict_files = [
        pth.dpd_mdx_path,
        pth.dpd_mdd_path,
        pth.dpd_deconstructor_mdx_path,
        pth.dpd_deconstructor_mdd_path,
        pth.dpd_grammar_mdx_path,
        pth.dpd_grammar_mdd_path,
        pth.dpd_variants_mdd_path,
        pth.dpd_variants_mdx_path,
    ]

    for file in mdict_files:
        if not file.exists():
            pr.no("error")
            pr.red(f"mdict file not found: {file}")

    output_mdict_zip = pth.dpd_mdict_zip_path

    with ZipFile(
        output_mdict_zip, "w", compression=ZIP_DEFLATED, compresslevel=5
    ) as mdict_zip:
        for mdict_file in mdict_files:
            file_content = mdict_file.read_bytes()
            mdict_zip.writestr(mdict_file.name, file_content)

    pr.yes("ok")


def main():
    pr.tic()
    pr.title("rezipping goldendict and mdict")
    pth = ProjectPaths()
    zip_goldendict(pth)
    zip_mdict(pth)
    pr.toc()


if __name__ == "__main__":
    main()
