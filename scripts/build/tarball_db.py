#!/usr/bin/env python3

"""Tarball the db for sharing."""

from tools.configger import config_test
from tools.paths import ProjectPaths
from tools.printer import printer as pr
from tools.tarballer import create_tarball


def main():
    pr.tic()
    pr.title("tarballing db")

    if config_test("exporter", "tarball_db", "no"):
        pr.green_title("disabled in config.ini")
        pr.toc()
        return

    pth = ProjectPaths()
    create_tarball(
        tarball_name="dpd.db.tar.bz2",
        source_files=[pth.dpd_db_path],
        destination_dir=pth.share_dir,
        compression="bz2",
    )
    pr.toc()


if __name__ == "__main__":
    main()
