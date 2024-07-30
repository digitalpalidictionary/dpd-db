#!/usr/bin/env python3

# unzip other dict from local folder Download to the fileserver. And copy mdx to Sync 

from datetime import date
from zipfile import ZipFile
import os
import shutil

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
   'various pali&sk'
   
)

kd_dir = os.path.join(
   software_dir,
   'Ebook Readers Dictionary'
)

gd_local_dir = os.path.join(deva_dir, 'Documents', 'GoldenDict')

sync_mdict_dir = os.path.join(deva_dir, 'Mdict')

# "simsapa.zip", 

other_dicts_gd_files = ["whitney.zip", "peu.zip", "mw.zip", "dpr.zip", "cpd.zip", "bhs.zip"]

other_dicts_md_files = ["whitney.mdx", "peu.mdx", "mw.mdx", "dpr.mdx", "cpd.mdx", "bhs.mdx", "simsapa.zip"]


# Unzip ZIP files into gd_dir
for file in other_dicts_gd_files:
   file_path = os.path.join(downloads_dir, file)
   if os.path.exists(file_path):
      with ZipFile(file_path, 'r') as zipObj:
            zipObj.extractall(gd_dir)
      print(f"\033[1;32m {file} has been unpacked to the server folder \033[0m")
   else:
      print(f"\033[1;31m {file} is missing. Cannot proceed with unpacking. \033[0m")


# Unzip ZIP files into gd_local_dir
for file in other_dicts_gd_files:
   file_path = os.path.join(downloads_dir, file)
   if os.path.exists(file_path):
      with ZipFile(file_path, 'r') as zipObj:
            zipObj.extractall(gd_local_dir)
      print(f"\033[1;32m {file} has been unpacked to the local GoldenDict folder \033[0m")
      os.remove(file_path)
      print(f"\033[1;32m {file} removed from the {downloads_dir} \033[0m")
   else:
      print(f"\033[1;31m {file} is missing. Cannot proceed with unpacking. \033[0m")


# сopy MDX files into sync_mdict_dir
for file in other_dicts_md_files:
   file_path = os.path.join(downloads_dir, file)
   if os.path.exists(file_path):
      shutil.copy2(file_path, md_dir)
      print(f"\033[1;32m {file} copied to sync_mdict_dir \033[0m")
   else:
      print(f"\033[1;31m {file} is missing. Cannot proceed with moving. \033[0m")


# Move MDX files into md_dir
for file in other_dicts_md_files:
   file_path = os.path.join(downloads_dir, file)
   if os.path.exists(file_path):
      shutil.copy2(file_path, md_dir)
      print(f"\033[1;32m {file} copied to the server \033[0m")
      # Delete the original file
      os.remove(file_path)
      print(f"\033[1;32m {file} removed from the {downloads_dir} \033[0m")
   else:
      print(f"\033[1;31m {file} is missing. Cannot proceed with moving. \033[0m")




