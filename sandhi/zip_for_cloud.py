#!/usr/bin/env python3.10

import os
import zipfile
from pathlib import Path
from rich import print


def zip_for_cloud():
    print("[green]zipping for cloud", end=" ")

    exclude = [
        "backups",
        "csvs",
        "gui",
        "inflections",
        "sandhi/!old sandhi-splitter.py",
        "sandhi/output",
        "sandhi/__pycache__",
        "sandhi/xxx sandhi_splitter.py",
        "sandhi/xxx structure.txt",
        "scripts",
        "share",
        "xxx delete",
        ".git",
        ".vscode",
        "dpd.db",
        "makedb.sh",
        "README.md",
        ".gitignore",
        "sandhi.zip",
    ]

    zip_path = Path("./")
    zipfile_name = Path("sandhi.zip")

    def zipdir(path, ziph, exclude):
        for root, dirs, files in os.walk(path):
            for file in files:
                if any(os.path.relpath(os.path.join(root, file), path).startswith(e) for e in exclude):
                    continue
                ziph.write(os.path.join(root, file))

    with zipfile.ZipFile(zipfile_name, "w", zipfile.ZIP_DEFLATED) as zipf:
        zipdir(zip_path, zipf, exclude)

    print("[white]ok")


if __name__ == "__main__":
    zip_for_cloud()
