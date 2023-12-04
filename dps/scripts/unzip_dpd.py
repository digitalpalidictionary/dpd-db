#!/usr/bin/env python3

# unzip dpd from local folder share to the goldendict dir.

from datetime import date
from zipfile import ZipFile
import os

today = date.today()

# Print completion message in yellow color
print("\033[1;33m from exporter/ \033[0m")

# Assuming the script is in the 'Documents/dpd-db/dps/scripts' directory
script_dir = os.path.dirname(os.path.realpath(__file__))
deva_dir = os.path.abspath(os.path.join(script_dir, '..', '..', '..', '..'))

goldendict_dir = os.path.join(deva_dir, 'Documents', 'GoldenDict')
share_dir = os.path.join(deva_dir, 'Documents', 'dpd-db', 'exporter', 'share')

dpd_goldendict_src = os.path.join(share_dir, 'dpd.zip')

# Check if the source zip file exists
if not os.path.exists(dpd_goldendict_src):
    print("\033[1;31m Error: dpd.zip not found in the specified source directory \033[0m")
else:
    try:
        # Unzip dpd_goldendict to the specified directory
        with ZipFile(dpd_goldendict_src, 'r') as zipObj:
            zipObj.extractall(goldendict_dir)

        # Print completion message in green color
        print("\033[1;32m dpd.zip has been unpacked to the GoldenDict folder \033[0m")
    except Exception as e:
        print("\033[1;31m An error occurred while extracting dpd.zip: \033[0m", str(e))
