#!/usr/bin/env python3

"""Tarball a list of files and move it to a destination folder."""

from pathlib import Path
import tarfile
import os

from tools.paths import ProjectPaths
from tools.printer import p_green, p_title, p_yes
from tools.tic_toc import tic, toc


def create_tarball(
    tarball_name: str, source_files: list[Path], destination_dir: Path, compression: str
) -> None:
    """
    Compression options are 'gz', 'bz2', 'zip' etc.
    """

    tic()
    p_title(f"Creating {tarball_name}")

    # add files
    p_green("adding files to tarball")

    with tarfile.open(tarball_name, f"w:{compression}") as tar:  # type: ignore
        for file in source_files:
            tar.add(file, arcname=os.path.basename(file))  # type: ignore
    p_yes(len(source_files))

    # get size
    p_green("tarball size")

    tar_size = os.path.getsize(tarball_name)
    tar_size_mb = tar_size / 1024 / 1024
    p_yes(f"{tar_size_mb:.3f}MB")

    # move to share folder
    p_green("moving to destination folder")

    os.rename(tarball_name, os.path.join(destination_dir, tarball_name))
    p_yes("ok")

    toc()


if __name__ == "__main__":
    pth = ProjectPaths()
    create_tarball(
        tarball_name="deconstructor_output.json.tar.gz",
        source_files=[pth.deconstructor_output_json],
        destination_dir=pth.deconstructor_output_dir,
        compression="gz",
    )
