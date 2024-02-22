"""
Setup deconstructor to run on cloud server,
include all necessary files and zip it up.
"""

import os
import shutil
import zipfile

from pathlib import Path
from rich import print

from tools.configger import config_update
from sandhi_setup import setup_deconstructor
from tools.tic_toc import tic, toc

def main():
    tic()
    print("[bright_yellow]setting up for deconstruction in the cloud")
    config_update("deconstructor", "run_on_cloud", "yes")
    config_update("deconstructor", "all_texts", "yes")
    setup_deconstructor()
    zip_for_cloud()
    move_zip()
    config_update("deconstructor", "run_on_cloud", "no")
    config_update("deconstructor", "all_texts", "no")
    toc()


def zip_for_cloud():
    print(f"[green]{'zipping for cloud':<35}", end="")

    include = [
        "config.ini",
        "README.md",
        "poetry.lock",
        "poetry.toml",
        "pyproject.toml",
        "db",
        "sandhi/assets",
        "sandhi/sandhi_related",
        "sandhi/books_to_include.py",
        "sandhi/helpers.py",
        "sandhi/sandhi_postprocess.py",
        "sandhi/sandhi_setup.py",
        "sandhi/sandhi_splitter.py",
        "sandhi/sandhi.sh",
        "tools"
    ]

    zip_path = Path("./")
    zipfile_name = Path("sandhi.zip")

    def zipdir(path, ziph, include):
        for root, __dirs__, files in os.walk(path):
            for file in files:
                if not any(
                        os.path.relpath(
                            os.path.join(root, file), path).startswith(i) for i in include):
                    continue
                ziph.write(os.path.join(root, file))

    with zipfile.ZipFile(zipfile_name, "w", zipfile.ZIP_DEFLATED) as zipf:
        zipdir(zip_path, zipf, include)

    print(f"[white]{'ok':>10}")


def move_zip():
    print(f"[green]{'moving zip':<35}", end="")
    shutil.move("sandhi.zip", "sandhi/sandhi.zip")
    print(f"[white]{'ok':>10}")


if __name__ == "__main__":
    main()