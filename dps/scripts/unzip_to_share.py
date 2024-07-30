#!/usr/bin/env python3

# unzip dpd-deconstructor and dpd-grammar from download folder to the share dir
from datetime import date
from zipfile import ZipFile
import os

today = date.today()

# Print completion message in yellow color
print("\033[1;33m from Downloads/ \033[0m")

# Assuming the script is in the 'Documents/dpd-db/dps/scripts' directory
script_dir = os.path.dirname(os.path.realpath(__file__))
deva_dir = os.path.abspath(os.path.join(script_dir, '..', '..', '..', '..'))


downloads_dir = os.path.join(deva_dir, 'Downloads')

share_dir = os.path.join(
    deva_dir, 
    'Documents', 
    'dpd-db',
    'exporter',
    'share'
)

dpd_goldendict_src = os.path.join(downloads_dir, 'dpd-goldendict.zip')
dpd_mdict_src = os.path.join(downloads_dir, 'dpd-mdict.zip')


if os.path.exists(dpd_goldendict_src):

    # Unzip dpd_goldendict to the specified directory
    with ZipFile(dpd_goldendict_src, 'r') as zipObj:
        # Get a list of all members in the archive
        members = zipObj.namelist()

        # Filter the members to only include the folders we want
        members_to_extract = [m for m in members if m.startswith('dpd-deconstructor/') or m.startswith('dpd-grammar/')]

        # Extract the filtered members
        zipObj.extractall(share_dir, members=members_to_extract)

    # Print completion message in green color
    print("\033[1;32m gdict deconstructor and grammar has been unpacked to share folder \033[0m")


if os.path.exists(dpd_mdict_src):
    # Unzip dpd_mdict to the specified directory
    with ZipFile(dpd_mdict_src, 'r') as zipObj:

        # Get a list of all members in the archive
        members = zipObj.namelist()

        # Filter the members to only include the specific files we want
        files_to_extract = [
            'dpd-grammar-mdict.mdx',
            'dpd-grammar-mdict.mdd',
            'dpd-deconstructor-mdict.mdd',
            'dpd-deconstructor-mdict.mdx'
        ]
        members_to_extract = [m for m in members if m in files_to_extract]

        # Extract the filtered members
        zipObj.extractall(share_dir, members=members_to_extract)

    # Print completion message in green color
    print("\033[1;32m mdict deconstructor and grammar has been unpacked to share \033[0m")  


