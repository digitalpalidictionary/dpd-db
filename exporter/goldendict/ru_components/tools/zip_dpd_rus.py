#!/usr/bin/env python3

"""
zip DPD+RUS into one: 
1. dpd foldter to dpd+rus-mdict.zip, 
2. dpd.mdx .mdd, into  dpd+rus-goldendict.zip
"""

import os
from zipfile import ZipFile, ZIP_DEFLATED
from tools.paths import ProjectPaths
from tools.tic_toc import bip, tic, toc
from tools.printer import p_title, p_green_title, p_red, p_yes, p_no


def zip_goldendict(pth: ProjectPaths):
    """Zip up dpd folder"""
    p_green_title("zipping ru goldendict")
    bip()
    
    if pth.dpd_goldendict_dir.exists():
        output_zip_file = os.path.join(pth.share_dir, "dpd+rus-goldendict.zip")

        with ZipFile(output_zip_file, "w", compression=ZIP_DEFLATED, compresslevel=5) as output_zip:
            for root, dirs, files in os.walk(pth.dpd_goldendict_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    # Calculate the relative path from the root of the input directory
                    relative_path = os.path.relpath(file_path, pth.dpd_goldendict_dir)
                    output_zip.write(file_path, relative_path)

        p_yes("ok")
    else:
        p_no("error")
        p_red("no ru-dpd dir file found")


def zip_mdict(pth: ProjectPaths):
    """Zipping up MDict files for sharing."""

    p_green_title("zipping mdict")
    bip()

    mdict_files = [
        pth.mdict_mdx_path,
        pth.mdict_mdd_path,
    ]

    for file in mdict_files:
        if not file.exists():
            p_no("error")
            p_red("mdict file found")
            return
    
    output_mdict_zip = os.path.join(pth.share_dir, "dpd+rus-mdict.zip")

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
    p_title("zipping dpd-rus for goldendict and mdict")
    pth = ProjectPaths()
    zip_goldendict(pth)
    zip_mdict(pth)
    toc()


if __name__ == "__main__":
    main()