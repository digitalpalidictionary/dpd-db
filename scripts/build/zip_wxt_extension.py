#!/usr/bin/env python3
"""Build and zip the WXT browser extension for Chrome and Firefox."""

import subprocess
from pathlib import Path
from tools.printer import printer as pr


def build_and_zip():
    pr.tic()
    pr.yellow_title("building and zipping WXT extensions")

    extension_dir = Path("exporter/wxt_extension")
    if not extension_dir.exists():
        pr.red(f"error: directory {extension_dir} not found.")
        return

    try:
        # Run the combined package command from package.json
        subprocess.run(["npm", "run", "package"], cwd=extension_dir, check=True)

        output_dir = extension_dir / ".output"
        zips = list(output_dir.glob("*.zip"))

        if zips:
            pr.green("created zip files in exporter/wxt_extension/.output/:")
            for zip_file in zips:
                pr.green(f" - {zip_file.name}")
        else:
            pr.red("\nBuild finished, but no zip files were found in .output/")

    except subprocess.CalledProcessError as e:
        pr.red("error during build/zip process:")
        pr.red(f"{e}")
    except Exception as e:
        pr.red("an unexpected error occurred")
        pr.red(f"{e}")

    pr.toc()


if __name__ == "__main__":
    build_and_zip()
