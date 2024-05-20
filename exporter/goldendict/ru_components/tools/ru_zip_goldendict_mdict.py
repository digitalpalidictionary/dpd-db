#!/usr/bin/env python3

"""Rezip the three files RU-DPD into one:
1. ru-dpd.zip, 2. ru-dpd-grammar.zip, 3. ru-dpd-deconstructor.zip
1. ru-dpd.mdx .mdd, 2. ru-dpd-grammar.mdx .mdd, 3. ru-dpd-deconstructor.mdx .mdd"""

import os
from zipfile import ZipFile, ZIP_DEFLATED
from exporter.goldendict.ru_components.tools.paths_ru import RuPaths
from tools.tic_toc import bip, tic, toc
from tools.printer import p_title, p_green_title, p_red, p_yes, p_no


def zip_goldendict(rupth: RuPaths):
    """Zip up the three dirs for goldendict"""
    p_green_title("zipping ru goldendict")
    bip()
    
    if (
        rupth.dpd_goldendict_dir.exists()
        and rupth.grammar_dict_goldendict_dir.exists()
        and rupth.deconstructor_goldendict_dir.exists()
    ):
        input_dirs = [
            (rupth.dpd_goldendict_dir, "ru-dpd"),
            (rupth.grammar_dict_goldendict_dir, "ru-dpd-grammar"),
            (rupth.deconstructor_goldendict_dir, "ru-dpd-deconstructor")]

        output_zip_file = rupth.dpd_goldendict_zip_path

        with ZipFile(output_zip_file, "w", compression=ZIP_DEFLATED, compresslevel=5) as output_zip:
            for input_dir, dir_name in input_dirs:
                for root, dirs, files in os.walk(input_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        # Calculate the relative path from the root of the input directory
                        relative_path = os.path.relpath(file_path, input_dir)
                        # Prepend the directory name to the relative path
                        archive_name = os.path.join(dir_name, relative_path)
                        output_zip.write(file_path, archive_name)

        p_yes("ok")
    else:
        p_no("error")
        p_red("no ru-dpd dir file found")


def zip_mdict(rupth: RuPaths):
    """Zipping up MDict files for sharing."""

    p_green_title("zipping mdict")
    bip()

    mdict_files = [
        rupth.mdict_mdx_path,
        rupth.mdict_mdd_path,
        rupth.deconstructor_mdx_path,
        rupth.deconstructor_mdd_path,
        rupth.grammar_dict_mdx_path,
        rupth.grammar_dict_mdd_path
    ]

    for file in mdict_files:
        if not file.exists():
            p_no("error")
            p_red("mdict file found")
            return
    
    output_mdict_zip = rupth.dpd_mdict_zip_path

    with ZipFile(
        output_mdict_zip, "w",
        compression=ZIP_DEFLATED,
        compresslevel=5
    ) as mdict_zip:
        for mdict_file in mdict_files:
            file_content = mdict_file.read_bytes()
            mdict_zip.writestr(mdict_file.name, file_content)

    p_yes("ok")


def main():
    tic()
    p_title("rezipping ru goldendict and mdict")
    rupth = RuPaths()
    zip_goldendict(rupth)
    zip_mdict(rupth)
    toc()


if __name__ == "__main__":
    main()