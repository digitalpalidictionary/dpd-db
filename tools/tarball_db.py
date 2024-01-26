

import tarfile
import zipfile
import os

from rich import print
from tools.paths import ProjectPaths
from tools.tic_toc import bip, bop

def main():
    print("[bright_yellow]zipping db to share")
    pth = ProjectPaths()
    tarballer(pth)
    zipper(pth)


def tarballer(pth):
    bip()
    print(f"{'tarballer':<20}", end="")

    tarname = "dpd.db.tar.gz"
    source_file = pth.dpd_db_path
    destination_dir = pth.zip_dir

    with tarfile.open("dpd.db.tar.gz", "w:gz", compresslevel=9) as tar:
        tar.add(source_file, arcname="dpd.db")
    print(f"{bop()} sec")

    # get size
    tar_size = os.path.getsize(tarname)
    tar_size_mb = tar_size / 1024 / 1024
    print(f"{'tarball size':<20}{tar_size_mb} MB")

    # move to share folder
    os.rename(tarname, os.path.join(destination_dir, tarname))
    
    
def zipper(pth):
    bip()
    print(f"{'zipper':<20}", end="")

    zipname = "dpd.db.zip"
    source_file = pth.dpd_db_path
    destination_dir = pth.zip_dir

    with zipfile.ZipFile(zipname, "w", compression=zipfile.ZIP_LZMA, compresslevel=5) as zipf:
        zipf.write(source_file, arcname="dpd.db")
    print(f"{bop()} sec")

    # get size
    zip_size = os.path.getsize(zipname)
    zip_size_mb = zip_size / 1024 / 1024
    print(f"{'zip size':<20}{zip_size_mb} MB")

    # move to share folder
    os.rename("dpd.db.zip", os.path.join(destination_dir, "dpd.zip"))
    
if __name__ == "__main__":
    main()