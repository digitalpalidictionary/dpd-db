#!/usr/bin/env python3

# unpack mdict ru to the Sync folder.

from datetime import date
import os
from tools.configger import config_test
from zipfile import ZipFile

today = date.today()

# Print completion message in green color
print("\033[1;33m unpacking mdict ru from exporter/share \033[0m")


# check config
if config_test("dictionary", "make_mdict", "yes"):

   # Assuming the script is in the 'Documents/dpd-db/dps/scripts' directory
   script_dir = os.path.dirname(os.path.realpath(__file__))
   deva_dir = os.path.abspath(os.path.join(script_dir, '..', '..', '..', '..'))

   sync_mdict_dir = os.path.join(deva_dir, 'Mdict')

   share_dir = os.path.join(
      deva_dir, 
      'Documents', 
      'dpd-db',
      'exporter',
      'share'
   )

   dpd_mdict_src = os.path.join(share_dir, 'ru-dpd-mdict.zip')

   if os.path.exists(dpd_mdict_src):
      # Unzip dpd_goldendict to the specified directory
      with ZipFile(dpd_mdict_src, 'r') as zipObj:
         # Extract all the contents of zip file in current directory
         zipObj.extractall(sync_mdict_dir)

      # Print completion message in green color
      print("\033[1;32m ru-dpd-mdict.zip has been unpacked to the sync folder \033[0m")
   else:
      print("\033[1;31m ru-dpd-mdict.zip is missing. Cannot proceed with moving. \033[0m")

else:
   print("moving is disabled in the config")





