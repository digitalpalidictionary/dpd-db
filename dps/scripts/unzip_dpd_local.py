#!/usr/bin/env python3

# unzip dpd from local folder share to the fileserver.

from datetime import date
from zipfile import ZipFile
import os

today = date.today()

# Print completion message in green color
print("\033[1;33m from exporter/share \033[0m")

# Assuming the script is in the 'Documents/dpd-db/dps/scripts' directory
script_dir = os.path.dirname(os.path.realpath(__file__))
deva_dir = os.path.abspath(os.path.join(script_dir, '..', '..', '..', '..'))

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

mdict_dir = os.path.join(
   software_dir,
   'MDict',
   'dpd'
)


share_dir = os.path.join(
   deva_dir, 
   'Documents', 
   'dpd-db',
   'exporter',
   'share'
)

dpd_goldendict_src = os.path.join(share_dir, 'dpd-goldendict.zip')
dpd_mdict_src = os.path.join(share_dir, 'dpd-mdict.zip')


if os.path.exists(dpd_goldendict_src):
   # Unzip dpd_goldendict to the specified directory
   with ZipFile(dpd_goldendict_src, 'r') as zipObj:
      # Extract all the contents of zip file in current directory
      zipObj.extractall(gd_dir)

   # Print completion message in green color
   print("\033[1;32m dpd.zip has been unpacked to the server folder \033[0m")


if os.path.exists(dpd_mdict_src):
   # Unzip dpd_mdict to the specified directory
   with ZipFile(dpd_mdict_src, 'r') as zipObj:
      # Extract all the contents of zip file in current directory
      zipObj.extractall(mdict_dir)
   # Print completion message in green color
   print("\033[1;32m dpd_mdict.zip has been unpacked to the server folder \033[0m")
else:
   print("\033[1;31m dpd_mdict.zip is missing. Cannot proceed with moving. \033[0m")



