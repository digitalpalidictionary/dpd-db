#!/usr/bin/env python3

"""Rezip the three files DPD into one:
1. dpd.zip, 2. dpd-grammar.zip, 3. dpd-deconstructor.zip
1. dpd.mdx, 2. dpd-grammar.mdx, 3. dpd-deconstructor.mdx"""

import os
from rich import print
from zipfile import ZipFile, ZIP_DEFLATED
from tools.paths import ProjectPaths
from tools.tic_toc import tic, toc

def main():
    tic()
    print("[bright_yellow]rezipping goldendict and mdict")
    pth = ProjectPaths()
    rezip_goldendict(pth)
    rezip_mdict(pth)
    toc()


def rezip_goldendict(pth: ProjectPaths):
    
    if (
        pth.dpd_zip_path.exists()
        and pth.grammar_dict_zip_path.exists()
        and pth.deconstructor_zip_path.exists()
    ):
        input_zip_files = [pth.dpd_zip_path,
                        pth.grammar_dict_zip_path,
                        pth.deconstructor_zip_path]

        output_zip_file = pth.dpd_goldendict_zip_path

        with ZipFile(output_zip_file, "w",
                    compression=ZIP_DEFLATED,
                    compresslevel=5) as output_zip:
            for input_zip_file in input_zip_files:
                with ZipFile(input_zip_file, "r") as input_zip:
                    for file_info in input_zip.infolist():
                        file_content = input_zip.read(file_info.filename)

                        # Extract the subdirectory name (e.g., 'dpd-grammar')
                        subdirectory_name = os.path.dirname(file_info.filename)
                        
                        # Construct the output path to include only the file's name with the subdirectory
                        output_path = f"{subdirectory_name}/{os.path.basename(file_info.filename)}"

                        # Add the file to the output zip
                        output_zip.writestr(output_path, file_content)

        print(f"{output_zip_file.name} created successfully.")
    
    else:
        print("[red]no dpd.zip file found")


def rezip_mdict(pth: ProjectPaths):

    if (
        pth.mdict_mdx_path.exists() 
        and pth.deconstructor_mdict_mdx_path.exists() 
        and pth.grammar_dict_mdict_path.exists()
    ):
        mdict_files = [pth.deconstructor_mdict_mdx_path,
                    pth.grammar_dict_mdict_path,
                    pth.mdict_mdx_path]

        output_mdict_zip = pth.dpd_mdict_zip_path

        with ZipFile(
            output_mdict_zip, "w",
            compression=ZIP_DEFLATED,
            compresslevel=5
        ) as mdict_zip:
            for mdict_file in mdict_files:
                file_content = mdict_file.read_bytes()
                mdict_zip.writestr(mdict_file.name, file_content)

        print(f"{output_mdict_zip.name} created successfully.")
    
    else:
        print("[red]no mdict file found")


if __name__ == "__main__":
    main()