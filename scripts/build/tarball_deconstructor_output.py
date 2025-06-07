#!/usr/bin/env python3

"""
Tarball the deconstructor output json file,
and copy to the resources folder.
"""

from tools.configger import config_test
from tools.paths import ProjectPaths
from tools.printer import printer as pr
from tools.tarballer import create_tarball


def main():
    pr.tic()
    pr.title("tarballing deconstructor output")

    if config_test("deconstructor", "use_premade", "yes"):
        pr.green_title("disabled in config.ini")
        pr.toc()
        return

    pth = ProjectPaths()

    source_path = pth.go_deconstructor_output_json
    dest_path = pth.deconstructor_output_json

    # Ensure the destination directory exists
    dest_path.parent.mkdir(parents=True, exist_ok=True)

    pr.green("copying from go dir")
    try:
        dest_path.write_bytes(source_path.read_bytes())
        pr.yes("ok")
    except Exception as e:
        pr.no(f"Error copying file: {e}")
        pr.toc()
        return

    create_tarball(
        tarball_name="deconstructor_output.json.tar.gz",
        source_files=[dest_path],  # Use the copied file path
        destination_dir=pth.deconstructor_output_dir,  # This is dest_path.parent
        compression="gz",
    )

    pr.toc()


if __name__ == "__main__":
    main()
