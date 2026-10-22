#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Tarball a list of files and move it to a destination folder."""

import os
import tarfile
from pathlib import Path

from tools.printer import printer as pr


def create_tarball(
    tarball_name: str, source_files: list[Path], destination_dir: Path, compression: str
) -> None:
    """
    Create a tarball of of a file list and move it to the destination dir.
    """
    pr.green_title(f"archiving {tarball_name}")

    pr.white_tmr("adding files")
    with tarfile.open(tarball_name, f"w:{compression}") as tar:  # type: ignore
        for file in source_files:
            tar.add(file, arcname=os.path.basename(file))
    pr.yes("ok")

    pr.white_tmr("tarball size in MB")
    tar_size = os.path.getsize(tarball_name)
    tar_size_mb = tar_size / 1024 / 1024
    pr.yes(f"{tar_size_mb:.3f}")

    pr.white_tmr("moving to destination folder")
    os.rename(tarball_name, os.path.join(destination_dir, tarball_name))
    pr.yes("ok")


def extract_tarball(
    tarball_path: Path, destination_dir: Path, preserve_structure: bool = True
) -> None:
    """
    Extract a tarball to the destination directory.

    Args:
        tarball_path: Path to the tarball file
        destination_dir: Directory to extract to
        preserve_structure: If True, preserve the directory structure from the tarball
                           If False, flatten the structure
    """
    pr.green_title(f"extracting {tarball_path.name}")

    if not tarball_path.exists():
        raise FileNotFoundError(f"Tarball not found: {tarball_path}")

    # Create destination directory if it doesn't exist
    destination_dir.mkdir(parents=True, exist_ok=True)

    pr.green_tmr("extracting files")
    with tarfile.open(tarball_path, "r:*") as tar:
        for member in tar.getmembers():
            # "data" refuses names that leave the folder, links and device files.
            # No mkdir from the raw member name first: it would create folders
            # outside the destination before the filter could refuse the member.
            tar.extract(member, destination_dir, filter="data")

    pr.yes("ok")
