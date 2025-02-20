#!/usr/bin/env python3

"""
Tarball the deconstructor output json file,
and copy to the resources folder.
"""

from tools.configger import config_test
from tools.paths import ProjectPaths
from tools.printer import p_green_title, p_title
from tools.tarballer import create_tarball
from tools.tic_toc import tic, toc


def main():

    tic()
    p_title("tarballing deconstructor output")

    if config_test("deconstructor", "use_premade", "yes"):
        p_green_title("disabled in config.ini")
        toc()
        return
    
    pth = ProjectPaths()
    create_tarball(
        tarball_name="deconstructor_output.json.tar.gz",
        source_files=[pth.deconstructor_output_json],
        destination_dir=pth.deconstructor_output_dir,
        compression="gz",
    )

    toc()


if __name__ == "__main__":
    main()
