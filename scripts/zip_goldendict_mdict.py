#!/usr/bin/env python3

"""Rezip the three files DPD into one:
1. dpd.zip, 2. dpd-grammar.zip, 3. dpd-deconstructor.zip
1. dpd.mdx .mdd, 2. dpd-grammar.mdx .mdd, 3. dpd-deconstructor.mdx .mdd"""

import os
from zipfile import ZipFile, ZIP_DEFLATED
from tools.paths import ProjectPaths
from tools.tic_toc import bip, tic, toc
from tools.printer import p_title, p_green, p_red, p_yes, p_no


def zip_goldendict(pth: ProjectPaths):
    """Zip up the three dirs for goldendict"""
    p_green("zipping goldendict")
    bip()
    
    if (
        pth.dpd_goldendict_dir.exists()
        and pth.grammar_dict_goldendict_dir.exists()
        and pth.deconstructor_goldendict_dir.exists()
    ):
        input_dirs = [
            (pth.dpd_goldendict_dir, "dpd"),
            (pth.grammar_dict_goldendict_dir, "dpd-grammar"),
            (pth.deconstructor_goldendict_dir, "dpd-deconstructor")]

        output_zip_file = pth.dpd_goldendict_zip_path

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
        p_red("no dpd dir file found")


def zip_mdict(pth: ProjectPaths):
    """Zipping up MDict files for sharing."""

    p_green("zipping mdict")
    bip()

    mdict_files = [
        pth.mdict_mdx_path,
        pth.mdict_mdd_path,
        pth.deconstructor_mdx_path,
        pth.deconstructor_mdd_path,
        pth.grammar_dict_mdx_path,
        pth.grammar_dict_mdd_path
    ]

    for file in mdict_files:
        if not file.exists():
            p_no("error")
            p_red("mdict file found")
            return
    
    output_mdict_zip = pth.dpd_mdict_zip_path

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
    p_title("rezipping goldendict and mdict")
    pth = ProjectPaths()
    zip_goldendict(pth)
    zip_mdict(pth)
    toc()


if __name__ == "__main__":
    main()