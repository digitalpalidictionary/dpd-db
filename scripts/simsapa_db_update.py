#!/usr/bin/env python3

"""Update the Simsapa db with latest DPD data."""

import subprocess

from rich import print

from tools.paths import ProjectPaths
from tools.tic_toc import tic, toc
from tools.configger import config_read, config_test

def main():
    tic()
    print("[bright_yellow]updating simsapa db")
    if config_test("exporter", "update_simsapa_db", "no"):
        print("[green]disable in config.ini")
    else:
        pth = ProjectPaths()
        simsapa_app_path = config_read("simsapa", "app_path")
        command = [simsapa_app_path, "migrate-and-index-dpd", pth.dpd_db_path]
        result = subprocess.run(command, capture_output=True, text=True)
        if result.returncode == 0:
            print("[green]updated ok")
            print(result.stdout)
        else:
            print("[red]update failed with return code:", result.returncode)
            print(result.stderr)
    toc()


if __name__ == "__main__":
    main()
