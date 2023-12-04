#!/usr/bin/env python3

# unzip dpd from local folder Download to the fileserver. And copy kindl version as well. 

from datetime import date
from zipfile import ZipFile
import os

today = date.today()

# Print completion message in green color
print("\033[1;33m from Downloads/ \033[0m")

# Assuming the script is in the 'Documents/dpd-db/dps/scripts' directory
script_dir = os.path.dirname(os.path.realpath(__file__))
deva_dir = os.path.abspath(os.path.join(script_dir, '..', '..', '..', '..'))

downloads_dir = os.path.join(deva_dir, 'Downloads')

software_dir = os.path.join(
   deva_dir,
   'filesrv1', 
   'share1', 
   'Sharing between users', 
   '1 For Everyone', 
   'Software'
)

gd_dir = os.path.join(
   software_dir,
   'Golden Dictionary', 
   'Default'
)

md_dir = os.path.join(
   software_dir, 
   'MDict', 
   'DPD'
)

dpd_kindle_mobi_src = os.path.join(downloads_dir, 'dpd-kindle.mobi')
dpd_kindle_mobi_dest = os.path.join(software_dir, 'dpd-kindle.mobi')

dpd_goldendict_src = os.path.join(downloads_dir, 'dpd-goldendict.zip')
dpd_mdict_src = os.path.join(downloads_dir, 'dpd-mdict.zip')

# Unzip dpd_goldendict to the specified directory
with ZipFile(dpd_goldendict_src, 'r') as zipObj:
   # Extract all the contents of zip file in current directory
   zipObj.extractall(gd_dir)

# Print completion message in green color
print("\033[1;32m dpd_goldendict.zip has been unpacked to the server folder \033[0m")

# Unzip dpd_mdict to the specified directory
with ZipFile(dpd_mdict_src, 'r') as zipObj:
   # Extract all the contents of zip file in current directory
   zipObj.extractall(md_dir)

# Print completion message in green color
print("\033[1;32m dpd_mdict.zip has been unpacked to the server folder \033[0m")

# Copy dpd-kindle.mobi to the specified directory
with open(dpd_kindle_mobi_src, 'rb') as src_file, open(dpd_kindle_mobi_dest, 'wb') as dest_file:
    dest_file.write(src_file.read())

# Print completion message for copying the file in green color
print("\033[1;32m dpd-kindle.mobi has been copied to the server folder \033[0m")



