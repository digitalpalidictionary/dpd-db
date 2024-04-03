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
   'MDict'
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
   'Kindle Dictionaries'
)

dpd_src = os.path.join(share_dir, 'ru-dpd.zip')
dpd_deconstructor_src = os.path.join(share_dir, 'ru-dpd-deconstructor.zip')
dpd_grammar_src = os.path.join(share_dir, 'ru-dpd-grammar.zip')

dpd_mdict_src = os.path.join(share_dir, 'ru-dpd-mdict.mdx')
dpd_mdict_dest = os.path.join(md_dir, 'ru-dpd-mdict.mdx')

dpd_deconstructor_mdict_src = os.path.join(share_dir, 'ru-dpd-deconstructor-mdict.mdx')
dpd_deconstructor_mdict_dest = os.path.join(md_dir, 'ru-dpd-deconstructor-mdict.mdx')

dpd_grammar_mdict_src = os.path.join(share_dir, 'ru-dpd-grammar-mdict.mdx')
dpd_grammar_mdict_dest = os.path.join(md_dir, 'ru-dpd-grammar-mdict.mdx')

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

if os.path.exists(dpd_deconstructor_src):
   # Unzip dpd_deconstructor to the specified directory
   with ZipFile(dpd_deconstructor_src, 'r') as zipObj:
      # Extract all the contents of zip file in current directory
      zipObj.extractall(gd_dir)
   # Print completion message in green color
   print("\033[1;32m ru_dpd_deconstructor.zip has been unpacked to the server folder \033[0m")
else:
   print("\033[1;31m ru_dpd_deconstructor.zip is missing. Cannot proceed with moving. \033[0m")

if os.path.exists(dpd_grammar_src):
   # Unzip dpd_grammar to the specified directory
   with ZipFile(dpd_grammar_src, 'r') as zipObj:
      # Extract all the contents of zip file in current directory
      zipObj.extractall(gd_dir)
   # Print completion message in green color
   print("\033[1;32m ru_dpd_grammar.zip has been unpacked to the server folder \033[0m")
else:
   print("\033[1;31m ru_dpd_grammar.zip is missing. Cannot proceed with moving. \033[0m")

# Copy dpd_mdict to the specified directory
if os.path.exists(dpd_mdict_src):
   shutil.copy2(dpd_mdict_src, dpd_mdict_dest)
   print("\033[1;32m dpd_mdict copied to the server \033[0m")
else:
   print("\033[1;31m dpd_mdict is missing. Cannot proceed with moving. \033[0m")

# Copy dpd_deconstructor_mdict to the specified directory
if os.path.exists(dpd_deconstructor_mdict_src):
   shutil.copy2(dpd_deconstructor_mdict_src, dpd_deconstructor_mdict_dest)
   print("\033[1;32m dpd_deconstructor_mdict copied to the server \033[0m")
else:
   print("\033[1;31m dpd_deconstructor_mdict is missing. Cannot proceed with moving. \033[0m")

# Copy dpd_grammar_mdict to the specified directory
if os.path.exists(dpd_grammar_mdict_src):
   shutil.copy2(dpd_grammar_mdict_src, dpd_grammar_mdict_dest)
   print("\033[1;32m dpd_grammar_mdict copied to the server \033[0m")
else:
   print("\033[1;31m dpd_grammar_mdict is missing. Cannot proceed with moving. \033[0m")

# Copy dpd-kindle.mobi to the specified directory
if os.path.exists(dpd_kindle_mobi_src):
   shutil.copy2(dpd_kindle_mobi_src, dpd_kindle_mobi_dest)
   print("\033[1;32m dpd_kindle.mobi copied to the server \033[0m")
else:
   print("\033[1;31m dpd_kindle.mobi is missing. Cannot proceed with moving. \033[0m")

# Copy dpd-kindle.epub to the specified directory
if os.path.exists(dpd_kindle_epub_src):
   shutil.copy2(dpd_kindle_epub_src, dpd_kindle_epub_dest)
   print("\033[1;32m dpd_kindle.epub copied to the server \033[0m")
else:
   print("\033[1;31m dpd_kindle.epub is missing. Cannot proceed with moving. \033[0m")





