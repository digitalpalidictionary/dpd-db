#!/usr/bin/env python3

# unzip rudpd from local folder share to the fileserver. And copy mdx and kindl versions as well. 

from datetime import date
from zipfile import ZipFile
import os
import shutil

today = date.today()

# Print completion message in green color
print("\033[1;33m from dpd-db/exporter/share/ \033[0m")

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
   'Optional'
)

md_dir = os.path.join(
   software_dir, 
   'MDict',
   'ru-dpd'
)

share_dir = os.path.join(
   deva_dir, 
   'Documents', 
   'dpd-db',
   'exporter',
   'share'
)

kd_dir = os.path.join(
   software_dir,
   'Ebook Readers Dictionary'
)

dpd_src = os.path.join(share_dir, 'ru-dpd-goldendict.zip')
dpd_mdict_src = os.path.join(share_dir, 'ru-dpd-mdict.zip')

dpd_kindle_mobi_src = os.path.join(share_dir, 'ru-dpd-kindle.mobi')
dpd_kindle_mobi_dest = os.path.join(kd_dir, 'ru-dpd-kindle.mobi')

dpd_kindle_epub_src = os.path.join(share_dir, 'ru-dpd-kindle.epub')
dpd_kindle_epub_dest = os.path.join(kd_dir, 'ru-dpd-kindle.epub')

if os.path.exists(dpd_src):
   # Unzip dpd to the specified directory
   with ZipFile(dpd_src, 'r') as zipObj:
      # Extract all the contents of zip file in current directory
      zipObj.extractall(gd_dir)
   # Print completion message in green color
   print("\033[1;32m ru_dpd.zip has been unpacked to the server folder \033[0m")
else:
   print("\033[1;31m ru_dpd.zip is missing. Cannot proceed with moving. \033[0m")

if os.path.exists(dpd_mdict_src):
   # Unzip dpd_mdict to the specified directory
   with ZipFile(dpd_mdict_src, 'r') as zipObj:
      # Extract all the contents of zip file in current directory
      zipObj.extractall(md_dir)
   # Print completion message in green color
   print("\033[1;32m ru_dpd_mdict.zip has been unpacked to the server folder \033[0m")
else:
   print("\033[1;31m ru_dpd_mdict.zip is missing. Cannot proceed with moving. \033[0m")

# Copy dpd-kindle.mobi to the specified directory
if os.path.exists(dpd_kindle_mobi_src):
   shutil.copy2(dpd_kindle_mobi_src, dpd_kindle_mobi_dest)
   print("\033[1;32m ru_dpd_kindle.mobi copied to the server \033[0m")
else:
   print("\033[1;31m ru_dpd_kindle.mobi is missing. Cannot proceed with moving. \033[0m")

# Copy dpd-kindle.epub to the specified directory
if os.path.exists(dpd_kindle_epub_src):
   shutil.copy2(dpd_kindle_epub_src, dpd_kindle_epub_dest)
   print("\033[1;32m ru_dpd_kindle.epub copied to the server \033[0m")
else:
   print("\033[1;31m ru_dpd_kindle.epub is missing. Cannot proceed with moving. \033[0m")





