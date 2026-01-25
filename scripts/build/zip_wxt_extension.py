#!/usr/bin/env python3
"""Build and zip the WXT browser extension for Chrome and Firefox."""

import subprocess
from pathlib import Path
from tools.printer import printer as pr


def build_and_zip():
    pr.tic()
    pr.title("building and zipping WXT extensions")

    extension_dir = Path("exporter/wxt_extension")
    if not extension_dir.exists():
        pr.error(f"error: directory {extension_dir} not found.")
        return

    try:
        # Run the combined package command from package.json
        subprocess.run(["npm", "run", "package"], cwd=extension_dir, check=True)

        output_dir = extension_dir / ".output"
        zips = list(output_dir.glob("*.zip"))

        if zips:
            pr.info("created zip files in exporter/wxt_extension/.output/:")
            for zip_file in zips:
                pr.info(f" - {zip_file.name}")
        else:
            pr.error("\nBuild finished, but no zip files were found in .output/")

    except subprocess.CalledProcessError as e:
        pr.error("error during build/zip process:")
        pr.error(f"{e}")
    except Exception as e:
        pr.error("an unexpected error occurred")
        pr.error(f"{e}")

    pr.toc()


if __name__ == "__main__":
    build_and_zip()
