#!/usr/bin/env python3

"""Tarball a list of files and move it to a destination folder."""

from pathlib import Path
import tarfile
import os

from tools.paths import ProjectPaths
from tools.printer import p_green, p_yes


def create_tarball(
        tarball_name: str, 
        source_files: list[Path], 
        destination_dir: Path, 
        compression: str
    ) -> None:
    """
    Create a tarball of of a file list and move it to the destination dir.
    """
    
    p_green(f"Creating {tarball_name}")
    with tarfile.open(tarball_name, f"w:{compression}") as tar: # type: ignore
        for file in source_files:
            tar.add(file, arcname=os.path.basename(file))
    p_yes("ok")

    # get size
    p_green("tarball size")
    tar_size = os.path.getsize(tarball_name)
    tar_size_mb = tar_size / 1024 / 1024
    p_yes(f"{tar_size_mb:.3f}MB")

    # move to share folder
    p_green("moving to destination folder")
    os.rename(tarball_name, os.path.join(destination_dir, tarball_name))   
    p_yes("ok")


if __name__ == "__main__":
    pth = ProjectPaths()

    create_tarball(
        tarball_name="deconstructor_output.json.tar.gz",
        source_files=[pth.deconstructor_output_json],
        destination_dir=pth.deconstructor_output_dir,
        compression="gz",
    )