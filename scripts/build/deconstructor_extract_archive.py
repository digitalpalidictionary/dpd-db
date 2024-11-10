#!/usr/bin/env python3

# unpack tar

import tarfile
import os

from tools.configger import config_test
from tools.paths import ProjectPaths
from tools.printer import p_green_title, p_green, p_red, p_title
from tools.tic_toc import tic, toc

def main():

    tic()
    p_title("extracting deconstructor archive")
    
    if not config_test("deconstructor", "use_premade", "yes"):
        p_green_title("disabled in config.ini")
        toc()
        return
    
    pth = ProjectPaths()
    input_archive = pth.deconstructor_output_tar_path
    output_directory = pth.deconstructor_output_dir
    
    # Ensure the output directory exists or create it
    os.makedirs(output_directory, exist_ok=True)
    
    # Open the tar.gz file and extract all contents
    try:
        with tarfile.open(input_archive, 'r:gz') as archive:
            for member in archive.getmembers():
                member_path = os.path.join(output_directory, member.name)
                if os.path.exists(member_path) and os.path.getmtime(member_path) == member.mtime:
                    p_green_title(f"{member.name} already exists and has the same date")
                else:
                    archive.extract(member, path=output_directory)
                    p_green_title(f"extracted {member.name}")
    except Exception as e:
        p_red(f"An error occurred:\n{e}") 

    toc()


if __name__ == "__main__":
    main()