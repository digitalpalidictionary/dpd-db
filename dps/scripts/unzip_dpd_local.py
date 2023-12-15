#!/usr/bin/env python3

# unzip dpd from local folder share to the fileserver.

from datetime import date
from zipfile import ZipFile
import os

today = date.today()

# Print completion message in green color
print("\033[1;33m from exporter/ \033[0m")

# Assuming the script is in the 'Documents/dpd-db/dps/scripts' directory
script_dir = os.path.dirname(os.path.realpath(__file__))
deva_dir = os.path.abspath(os.path.join(script_dir, '..', '..', '..', '..'))

software_dir = os.path.join(
   deva_dir,
   'filesrv1', 
   'share1', 
   'Sharing between users', 
   '1 For Everyone', 
   'Software',
   'Golden Dictionary', 
   'Default'
)


share_dir = os.path.join(
   deva_dir, 
   'Documents', 
   'dpd-db',
   'exporter',
   'share'
)

dpd_goldendict_src = os.path.join(share_dir, 'dpd.zip')


if os.path.exists(dpd_goldendict_src):
   # Unzip dpd_goldendict to the specified directory
   with ZipFile(dpd_goldendict_src, 'r') as zipObj:
      # Extract all the contents of zip file in current directory
      zipObj.extractall(software_dir)

   # Print completion message in green color
   print("\033[1;32m dpd.zip has been unpacked to the server folder \033[0m")


