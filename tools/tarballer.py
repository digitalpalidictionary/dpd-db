#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Tarball a list of files and move it to a destination folder."""

import os
import tarfile
from pathlib import Path

from tools.paths import ProjectPaths
from tools.printer import printer as pr


def create_tarball(
    tarball_name: str, source_files: list[Path], destination_dir: Path, compression: str
) -> None:
    """
    Create a tarball of of a file list and move it to the destination dir.
    """
    pr.green_title(f"Creating [white]{tarball_name}")

    pr.green("adding files")
    with tarfile.open(tarball_name, f"w:{compression}") as tar:  # type: ignore
        for file in source_files:
            tar.add(file, arcname=os.path.basename(file))
    pr.yes("ok")

    pr.green("tarball size in MB")
    tar_size = os.path.getsize(tarball_name)
    tar_size_mb = tar_size / 1024 / 1024
    pr.yes(f"{tar_size_mb:.3f}")

    pr.green("moving to destination folder")
    os.rename(tarball_name, os.path.join(destination_dir, tarball_name))
    pr.yes("ok")


if __name__ == "__main__":
    pth = ProjectPaths()

    create_tarball(
        tarball_name="deconstructor_output.json.tar.gz",
        source_files=[pth.deconstructor_output_json],
        destination_dir=pth.deconstructor_output_dir,
        compression="gz",
    )
