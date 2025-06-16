#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# unpack tar

import tarfile
import os

from tools.configger import config_test
from tools.paths import ProjectPaths
from tools.printer import printer as pr


def main():
    pr.tic()
    pr.title("extracting deconstructor archive")

    if not config_test("deconstructor", "use_premade", "yes"):
        pr.green_title("disabled in config.ini")
        pr.toc()
        return

    pth = ProjectPaths()
    input_archive = pth.deconstructor_output_tar_path
    output_directory = pth.deconstructor_output_dir

    # Ensure the output directory exists or create it
    os.makedirs(output_directory, exist_ok=True)

    # Open the tar.gz file and extract all contents
    try:
        with tarfile.open(input_archive, "r:gz") as archive:
            for member in archive.getmembers():
                member_path = os.path.join(output_directory, member.name)
                if (
                    os.path.exists(member_path)
                    and os.path.getmtime(member_path) == member.mtime
                ):
                    pr.green_title(
                        f"{member.name} already exists and has the same date"
                    )
                else:
                    archive.extract(member, path=output_directory)
                    pr.green_title(f"extracted {member.name}")
    except Exception as e:
        pr.red(f"An error occurred:\n{e}")

    pr.toc()


if __name__ == "__main__":
    main()
