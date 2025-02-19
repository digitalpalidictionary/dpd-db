#!/usr/bin/env python3

"""
Tarball the deconstructor output json file,
and copy to the resources folder.
"""

from tools.paths import ProjectPaths
from tools.tarballer import create_tarball


def main():
    pth = ProjectPaths()
    create_tarball(
        tarball_name="deconstructor_output.json.tar.gz",
        source_files=[pth.deconstructor_output_json],
        destination_dir=pth.deconstructor_output_dir,
        compression="gz",
    )


if __name__ == "__main__":
    main()
