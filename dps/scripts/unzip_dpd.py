#!/usr/bin/env python3

# unip dpd from local folder Share inlt the GoldenDict folder 

from datetime import date
from zipfile import ZipFile
from tools.paths import ProjectPaths as PATH
from dps.tools.paths_dps import DPSPaths as DPSPATH


today = date.today()

with ZipFile(PATH.zip_path, 'r') as zipObj:
   # Extract all the contents of zip file in current directory
   zipObj.extractall(DPSPATH.local_goldendict_path)

# Print completion message in green color
print("\033[33m from dpd-db/exporter/share/ \033[0m")

# Print completion message in green color
print("\033[32m dpd.zip has been unpacked to the GoldenDict folder \033[0m")

with ZipFile(PATH.deconstructor_zip_path, 'r') as zipObj:
   # Extract all the contents of zip file in current directory
   zipObj.extractall(DPSPATH.local_goldendict_path)

# Print completion message in green color
print("\033[32m dpd-deconstructor.zip has been unpacked GoldenDict folder \033[0m")


with ZipFile(PATH.grammar_dict_zip_path, 'r') as zipObj:
   # Extract all the contents of zip file in current directory
   zipObj.extractall(DPSPATH.local_goldendict_path)


# Print completion message in green color
print("\033[32m dpd-grammar.zip has been unpacked to the GoldenDict folder \033[0m")


