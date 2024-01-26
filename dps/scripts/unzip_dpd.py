#!/usr/bin/env python3

# unzip dpd from download folder to the goldendict dir.

from datetime import date
from zipfile import ZipFile
import os

today = date.today()

# Print completion message in yellow color
print("\033[1;33m from Downloads/ \033[0m")

# Assuming the script is in the 'Documents/dpd-db/dps/scripts' directory
script_dir = os.path.dirname(os.path.realpath(__file__))
deva_dir = os.path.abspath(os.path.join(script_dir, '..', '..', '..', '..'))

goldendict_dir = os.path.join(deva_dir, 'Documents', 'GoldenDict')

downloads_dir = os.path.join(deva_dir, 'Downloads')

sync_mdict_dir = os.path.join(deva_dir, 'Mdict')

dpd_goldendict_src = os.path.join(downloads_dir, 'dpd-goldendict.zip')
dpd_mdict_src = os.path.join(downloads_dir, 'dpd-mdict.zip')


if os.path.exists(dpd_goldendict_src):

    # Unzip dpd_goldendict to the specified directory
    with ZipFile(dpd_goldendict_src, 'r') as zipObj:
        # Extract all the contents of zip file in current directory
        zipObj.extractall(goldendict_dir)

    # Print completion message in green color
    print("\033[1;32m dpd_goldendict.zip has been unpacked locally \033[0m")


if os.path.exists(dpd_mdict_src):
    # Unzip dpd_mdict to the specified directory
    with ZipFile(dpd_mdict_src, 'r') as zipObj:
        # Extract all the contents of zip file in current directory
        zipObj.extractall(sync_mdict_dir)
    # Print completion message in green color
    print("\033[1;32m dpd_mdict.zip has been unpacked to MDict folder, please Sync \033[0m")  


