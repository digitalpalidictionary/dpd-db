#!/usr/bin/env python3

"""Rezip the three files RU-DPD into one:
1. ru-dpd.zip, 2. ru-dpd-grammar.zip, 3. ru-dpd-deconstructor.zip
1. ru-dpd.mdx .mdd, 2. ru-dpd-grammar.mdx .mdd, 3. ru-dpd-deconstructor.mdx .mdd"""

import os
from zipfile import ZipFile, ZIP_DEFLATED
from dps.scripts.rus_exporter.paths_ru import RuPaths
from tools.printer import printer as pr


def zip_goldendict(rupth: RuPaths):
    """Zip up the three dirs for goldendict"""
    pr.green_title("zipping ru goldendict")

    if (
        rupth.dpd_goldendict_dir.exists()
        and rupth.grammar_dict_goldendict_dir.exists()
        and rupth.deconstructor_goldendict_dir.exists()
    ):
        input_dirs = [
            (rupth.dpd_goldendict_dir, "ru-dpd"),
            (rupth.grammar_dict_goldendict_dir, "ru-dpd-grammar"),
            (rupth.deconstructor_goldendict_dir, "ru-dpd-deconstructor"),
        ]

        output_zip_file = rupth.dpd_goldendict_zip_path

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
        pr.red("no ru-dpd dir file found")


def zip_mdict(rupth: RuPaths):
    """Zipping up MDict files for sharing."""

    pr.green_title("zipping mdict")

    mdict_files = [
        rupth.mdict_mdx_path,
        rupth.mdict_mdd_path,
        rupth.deconstructor_mdx_path,
        rupth.deconstructor_mdd_path,
        rupth.grammar_dict_mdx_path,
        rupth.grammar_dict_mdd_path,
    ]

    for file in mdict_files:
        if not file.exists():
            pr.no("error")
            pr.red("mdict file not found")
            return

    output_mdict_zip = rupth.dpd_mdict_zip_path

    with ZipFile(
        output_mdict_zip, "w", compression=ZIP_DEFLATED, compresslevel=5
    ) as mdict_zip:
        for mdict_file in mdict_files:
            file_content = mdict_file.read_bytes()
            mdict_zip.writestr(mdict_file.name, file_content)

    pr.yes("ok")


def main():
    pr.tic()
    pr.title("rezipping ru goldendict and mdict")
    rupth = RuPaths()
    zip_goldendict(rupth)
    zip_mdict(rupth)
    pr.toc()


if __name__ == "__main__":
    main()
