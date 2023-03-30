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
        "definitions",
        "exporter",
        "family_compound",
        "family_root",
        "family_set",
        "family_word",
        "frequency",
        "grammar_dict",
        "gui",
        "inflections",

        "sandhi/output",
        "output_do",
        "sandhi/__pycache__",
        "sandhixxx old sandhi-splitter.py"
        "sandhi/xxx sandhi_splitter.py",

        "scripts",
        "share",
        "tests",
        "xxx delete",
        ".git",
        ".venv",
        ".vscode",
        "do_output.zip",
        "dpd.db",
        "exporter.code-workspace",
        "README.md",
        "sandhi.zip",
        ".gitignore",
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


def zip_for_cloud_include():
    print("[green]zipping for cloud", end=" ")

    include = [
        "poetry.lock",
        "poetry.toml",
        "pyproject.toml",
        "README.md",
        "db",
        "sandhi/assets",
        "sandhi/sandhi_related",
        "sandhi/books_to_include.py",
        "sandhi/helpers.py",
        "sandhi/postprocess.py",
        "sandhi/setup.py",
        "sandhi/splitter.py",
        "tools"
    ]

    zip_path = Path("./")
    zipfile_name = Path("sandhi.zip")

    def zipdir(path, ziph, include):
        for root, dirs, files in os.walk(path):
            for file in files:
                if not any(
                        os.path.relpath(
                            os.path.join(root, file), path).startswith(i) for i in include):
                    continue
                ziph.write(os.path.join(root, file))

    with zipfile.ZipFile(zipfile_name, "w", zipfile.ZIP_DEFLATED) as zipf:
        zipdir(zip_path, zipf, include)

    print("[white]ok")



if __name__ == "__main__":
    zip_for_cloud_include()
