#!/usr/bin/env python3

"""Rezip the three files RU-DPD into one:
1. ru-dpd.zip, 2. ru-dpd-grammar.zip, 3. ru-dpd-deconstructor.zip
1. ru-dpd.mdx, 2. ru-dpd-grammar.mdx, 3. ru-dpd-deconstructor.mdx"""

import os
from rich import print
from zipfile import ZipFile, ZIP_DEFLATED
from exporter.ru_components.tools.paths_ru import RuPaths
from tools.tic_toc import tic, toc

def main():
    tic()
    print("[bright_yellow]rezipping goldendict ru and mdict ru")
    rupth = RuPaths()
    rezip_goldendict_ru(rupth)
    rezip_mdict_ru(rupth)
    toc()


def rezip_goldendict_ru(rupth: RuPaths):
    
    if (
        rupth.dpd_output_dir.exists()
        and rupth.grammar_dict_dir.exists()
        and rupth.deconstructor_output_dir.exists()
    ):
        input_zip_files = [rupth.dpd_output_dir,
                        rupth.grammar_dict_dir,
                        rupth.deconstructor_output_dir]

        output_zip_file = rupth.dpd_goldendict_zip_path

        with ZipFile(output_zip_file, "w",
                    compression=ZIP_DEFLATED,
                    compresslevel=5) as output_zip:
            for input_zip_file in input_zip_files:
                with ZipFile(input_zip_file, "r") as input_zip:
                    for file_info in input_zip.infolist():
                        file_content = input_zip.read(file_info.filename)

                        # Extract the subdirectory name (e.g., 'ru-dpd-grammar')
                        subdirectory_name = os.path.dirname(file_info.filename)
                        
                        # Construct the output path to include only the file's name with the subdirectory
                        output_path = f"{subdirectory_name}/{os.path.basename(file_info.filename)}"

                        # Add the file to the output zip
                        output_zip.writestr(output_path, file_content)

        print(f"{output_zip_file.name} created successfully.")
    
    else:
        print("[red]no ru-dpd.zip file found")


def rezip_mdict_ru(rupth: RuPaths):

    if (
        rupth.mdict_mdx_path.exists() 
        and rupth.deconstructor_mdict_mdx_path.exists() 
        and rupth.grammar_dict_mdict_path.exists()
    ):
        mdict_files = [rupth.deconstructor_mdict_mdx_path,
                    rupth.grammar_dict_mdict_path,
                    rupth.mdict_mdx_path]

        output_mdict_zip = rupth.dpd_mdict_zip_path

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