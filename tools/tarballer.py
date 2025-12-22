#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Tarball a list of files and move it to a destination folder."""

import os
import tarfile
from pathlib import Path
from typing import Dict

from tools.paths import ProjectPaths
from tools.printer import printer as pr


def create_tarball(
    tarball_name: str, source_files: list[Path], destination_dir: Path, compression: str
) -> None:
    """
    Create a tarball of of a file list and move it to the destination dir.
    """
    pr.green_title(f"archiving {tarball_name}")

    pr.white("adding files")
    with tarfile.open(tarball_name, f"w:{compression}") as tar:  # type: ignore
        for file in source_files:
            tar.add(file, arcname=os.path.basename(file))
    pr.yes("ok")

    pr.white("tarball size in MB")
    tar_size = os.path.getsize(tarball_name)
    tar_size_mb = tar_size / 1024 / 1024
    pr.yes(f"{tar_size_mb:.3f}")

    pr.white("moving to destination folder")
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

    pr.green("extracting files")
    with tarfile.open(tarball_path, "r:*") as tar:
        for member in tar.getmembers():
            if preserve_structure:
                # Preserve the full path structure
                target_path = destination_dir / member.name
            else:
                # Flatten the structure - extract only the filename
                target_path = destination_dir / os.path.basename(member.name)

            # Create parent directories if needed
            target_path.parent.mkdir(parents=True, exist_ok=True)

            # Extract the file/directory
            tar.extract(member, destination_dir)

    pr.yes("ok")


def extract_tarball_to_paths(
    tarball_path: Path, base_dir: Path, extraction_map: Dict[str, str]
) -> None:
    """
    Extract specific files/directories from a tarball to specified locations.

    Args:
        tarball_path: Path to the tarball file
        base_dir: Base directory for extraction
        extraction_map: Dict mapping tarball paths to local paths
                       e.g., {"db/dpd_audio.db": "audio/db/dpd_audio.db"}
    """
    pr.green_title(f"Extracting [white]{tarball_path.name} with mapping")

    if not tarball_path.exists():
        raise FileNotFoundError(f"Tarball not found: {tarball_path}")

    with tarfile.open(tarball_path, "r:*") as tar:
        for member in tar.getmembers():
            if member.name in extraction_map:
                target_path = base_dir / extraction_map[member.name]
                target_path.parent.mkdir(parents=True, exist_ok=True)
                tar.extract(member, target_path.parent)
                temp_path = target_path.parent / member.name
                temp_path.rename(target_path)
                pr.yes(f"Extracted: {member.name} -> {extraction_map[member.name]}")


if __name__ == "__main__":
    pth = ProjectPaths()

    create_tarball(
        tarball_name="deconstructor_output.json.tar.gz",
        source_files=[pth.deconstructor_output_json],
        destination_dir=pth.deconstructor_output_dir,
        compression="gz",
    )
