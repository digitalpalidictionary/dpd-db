#!/usr/bin/env python3

# unpack tar

import tarfile
import os
import sys

from tools.configger import config_test
from tools.printer import p_green, p_title, p_red, p_yes
from tools.tic_toc import tic, toc

def extract_archive(input_archive, output_directory):
    # Ensure the output directory exists or create it
    os.makedirs(output_directory, exist_ok=True)
    
    # Open the tar.gz file and extract all contents
    try:
        with tarfile.open(input_archive, 'r:gz') as archive:
            for member in archive.getmembers():
                member_path = os.path.join(output_directory, member.name)
                if os.path.exists(member_path) and os.path.getmtime(member_path) == member.mtime:
                    p_green(f"{member.name} already exists and has the same date")
                else:
                    archive.extract(member, path=output_directory)
                    p_green(f"extracted {member.name}")
    except Exception as e:
        p_red(f"an error occurred: {e}")


def main():
    tic()
    p_title("extracting deconstructor output")
    # Ensure that both input_archive and output_directory are provided
    if len(sys.argv) != 3:
        p_green("Usage: python extract_archive.py <input_archive> <output_directory>")
        sys.exit(1)
    
    input_archive = sys.argv[1]
    output_directory = sys.argv[2]
    
    extract_archive(input_archive, output_directory)
    p_yes("ok")

    toc()

    
if __name__ == "__main__":
    if config_test("deconstructor", "include_cloud", "yes"):
        main()
    else:
        print("include_cloud is disabled")