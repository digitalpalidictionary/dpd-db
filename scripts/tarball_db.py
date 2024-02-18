

import tarfile
import os

from rich import print
from tools.paths import ProjectPaths
from tools.tic_toc import bip, bop


def main():
    print("[bright_yellow]compressing db to share")
    pth = ProjectPaths()
    create_tarball_bz2(pth)


def create_tarball_bz2(pth: ProjectPaths):
    bip()
    print(f"[green]{'tarballing dbd.dp':<20}", end="")

    tarball_name = "dpd.db.tar.bz2"
    source_file = pth.dpd_db_path
    destination_dir = pth.share_dir

    with tarfile.open(tarball_name, "w:bz2") as tar:
        tar.add(source_file, arcname="dpd.db")
    print(f"{bop()} sec")

    # get size
    tar_size = os.path.getsize(tarball_name)
    tar_size_mb = tar_size /  1024 /  1024
    print(f"[green]{'tarball size':<20}{tar_size_mb:.3f} MB")

    # move to share folder
    os.rename(tarball_name, os.path.join(destination_dir, tarball_name))


if __name__ == "__main__":
    main()
