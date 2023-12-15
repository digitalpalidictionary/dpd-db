#!/usr/bin/env python3

# move mdict to the Sync folder.

from datetime import date
import os
import shutil

today = date.today()

# Print completion message in green color
print("\033[1;33m from exporter/ \033[0m")

# Assuming the script is in the 'Documents/dpd-db/dps/scripts' directory
script_dir = os.path.dirname(os.path.realpath(__file__))
deva_dir = os.path.abspath(os.path.join(script_dir, '..', '..', '..', '..'))

sync_dir = os.path.join(deva_dir, 'Mdict')

share_dir = os.path.join(
   deva_dir, 
   'Documents', 
   'dpd-db',
   'exporter',
   'share'
)

dpd_mdict_src = os.path.join(share_dir, 'dpd-mdict.mdx')
dpd_grammar_mdict_src = os.path.join(share_dir, 'dpd-grammar-mdict.mdx')
dpd_deconstructor_mdict_src = os.path.join(share_dir, 'dpd-deconstructor-mdict.mdx')

dpd_mdict_dest = os.path.join(sync_dir, 'dpd-mdict.mdx')
dpd_grammar_mdict_dest = os.path.join(sync_dir, 'dpd-grammar-mdict.mdx')
dpd_deconstructor_mdict_dest = os.path.join(sync_dir, 'dpd-deconstructor-mdict.mdx')


# Move each file if it exists
if os.path.exists(dpd_mdict_src):
   shutil.move(dpd_mdict_src, dpd_mdict_dest)
   print("\033[1;32m dpd-mdict.mdx moved to Sync folder \033[0m")
else:
   print("\033[1;31m dpd-mdict.mdx is missing. Cannot proceed with moving. \033[0m")

if os.path.exists(dpd_grammar_mdict_src):
   shutil.move(dpd_grammar_mdict_src, dpd_grammar_mdict_dest)
   print("\033[1;32m dpd-grammar-mdict.mdx moved to Sync folder \033[0m")
else:
   print("\033[1;31m dpd-grammar-mdict.mdx is missing. Cannot proceed with moving. \033[0m")

if os.path.exists(dpd_deconstructor_mdict_src):
   shutil.move(dpd_deconstructor_mdict_src, dpd_deconstructor_mdict_dest)
   print("\033[1;32m dpd-deconstructor-mdict.mdx moved to Sync folder \033[0m")
else:
   print("\033[1;31m dpd-deconstructor-mdict.mdx is missing. Cannot proceed with moving. \033[0m")





