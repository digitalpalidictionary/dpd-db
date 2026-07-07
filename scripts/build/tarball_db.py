#!/usr/bin/env python3

"""Tarball the db for sharing.

Uses the xz CLI via `tar -I` — Python's stdlib lzma is single-threaded and
takes ~25 minutes on the 2.2GB db, `xz -9e -T0` takes ~4.5 minutes.
"""

import subprocess

from tools.configger import config_test
from tools.paths import ProjectPaths
from tools.printer import printer as pr


def main() -> None:
    pr.tic()
    pr.yellow_title("tarballing db")

    if config_test("exporter", "tarball_db", "no"):
        pr.green_title("disabled in config.ini")
        pr.toc()
        return

    pth = ProjectPaths()
    tarball_path = pth.share_dir / "dpd.db.tar.xz"

    pr.green_title(f"archiving {tarball_path.name}")

    pr.white_tmr("adding files")
    subprocess.run(
        [
            "tar",
            "-I",
            "xz -9e -T0",
            "-cf",
            str(tarball_path),
            "-C",
            str(pth.dpd_db_path.parent),
            pth.dpd_db_path.name,
        ],
        check=True,
    )
    pr.yes("ok")

    pr.white_tmr("tarball size in MB")
    tar_size_mb = tarball_path.stat().st_size / 1024 / 1024
    pr.yes(f"{tar_size_mb:.3f}")

    pr.toc()


if __name__ == "__main__":
    main()
