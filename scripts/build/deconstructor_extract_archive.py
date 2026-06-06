#!/usr/bin/env python3

import tarfile

from tools.configger import config_test
from tools.paths import ProjectPaths
from tools.printer import printer as pr


def main() -> None:
    pr.tic()
    pr.yellow_title("extracting deconstructor archive")

    if not config_test("deconstructor", "use_premade", "yes"):
        pr.green_title("disabled in config.ini")
        pr.toc()
        return

    pth = ProjectPaths()
    input_archive = pth.deconstructor_output_tar_path
    output_directory = pth.deconstructor_output_dir

    output_directory.mkdir(parents=True, exist_ok=True)

    try:
        with tarfile.open(input_archive, "r:gz") as archive:
            for member in archive.getmembers():
                member_path = output_directory / member.name
                if member_path.exists() and member_path.stat().st_mtime == member.mtime:
                    pr.green_title(
                        f"{member.name} already exists and has the same date"
                    )
                else:
                    archive.extract(member, path=output_directory, filter="data")
                    pr.green_title(f"extracted {member.name}")
    except Exception as e:
        pr.red(f"An error occurred:\n{e}")

    pr.toc()


if __name__ == "__main__":
    main()
