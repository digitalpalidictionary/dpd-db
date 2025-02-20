#!/usr/bin/env python3

"""Tarball the db for sharing."""

from tools.configger import config_test
from tools.paths import ProjectPaths
from tools.printer import p_green_title, p_title
from tools.tarballer import create_tarball
from tools.tic_toc import tic, toc


def main():

    tic()
    p_title("tarballing db")

    if config_test("exporter", "tarball_db", "no"):
        p_green_title("disabled in config.ini")
        toc()
        return

    pth = ProjectPaths()
    create_tarball(
        tarball_name="dpd.db.tar.bz2",
        source_files=[pth.dpd_db_path],
        destination_dir=pth.share_dir,
        compression="bz2"
    )
    toc()


if __name__ == "__main__":
    main()
    
