#!/usr/bin/env python3

# move mdict ru to the Sync folder.

from datetime import date
import os
import shutil
from tools.configger import config_test

today = date.today()

# Print completion message in green color
print("\033[1;33m moving mdict ru from exporter_ru/ \033[0m")


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

   dpd_mdict_src = os.path.join(share_dir, 'ru-dpd-mdict.mdx')
   # dpd_grammar_mdict_src = os.path.join(share_dir, 'dpd-grammar-mdict.mdx')
   # dpd_deconstructor_mdict_src = os.path.join(share_dir, 'dpd-deconstructor-mdict.mdx')

   dpd_mdict_dest = os.path.join(sync_mdict_dir, 'ru-dpd-mdict.mdx')
   # dpd_grammar_mdict_dest = os.path.join(sync_mdict_dir, 'dpd-grammar-mdict.mdx')
   # dpd_deconstructor_mdict_dest = os.path.join(sync_mdict_dir, 'dpd-deconstructor-mdict.mdx')


   # Move each file if it exists
   if os.path.exists(dpd_mdict_src):
      shutil.copy2(dpd_mdict_src, dpd_mdict_dest)
      print("\033[1;32m ru-dpd-mdict.mdx copied to Sync folder \033[0m")
   else:
      print("\033[1;31m ru-dpd-mdict.mdx is missing. Cannot proceed with moving. \033[0m")

   # if os.path.exists(dpd_grammar_mdict_src):
   #    shutil.copy2(dpd_grammar_mdict_src, dpd_grammar_mdict_dest)
   #    print("\033[1;32m dpd-grammar-mdict.mdx moved to Sync folder \033[0m")
   # else:
   #    print("\033[1;31m dpd-grammar-mdict.mdx is missing. Cannot proceed with moving. \033[0m")

   # if os.path.exists(dpd_deconstructor_mdict_src):
   #    shutil.copy2(dpd_deconstructor_mdict_src, dpd_deconstructor_mdict_dest)
   #    print("\033[1;32m dpd-deconstructor-mdict.mdx moved to Sync folder \033[0m")
   # else:
   #    print("\033[1;31m dpd-deconstructor-mdict.mdx is missing. Cannot proceed with moving. \033[0m")

else:
   print("moving is disabled in the config")





