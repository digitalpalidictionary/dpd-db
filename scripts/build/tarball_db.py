#!/usr/bin/env python3

from tools.paths import ProjectPaths
from tools.tarballer import create_tarball


def main():
    pth = ProjectPaths()
    create_tarball(
        tarball_name="dpd.db.tar.bz2",
        source_files=[pth.dpd_db_path],
        destination_dir=pth.share_dir,
        compression="bz2"
    )

if __name__ == "__main__":
    main()
    
