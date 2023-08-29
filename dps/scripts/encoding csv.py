
""" Encoding csv into utf-8 and save into csv (with backing up existing temp csv)"""

from dps.tools.paths_dps import DPSPaths as DPSPTH

import os
import shutil
from rich import print
from tools.tic_toc import tic, toc
from datetime import datetime

tic()

original_file = DPSPTH.sbs_index_path
new_file = DPSPTH.temp_csv_path

with open(original_file, 'r') as source_file:
    content = source_file.read()

# Check if the CSV exists, and create a backup with a timestamp if it does
if os.path.exists(DPSPTH.temp_csv_path):
    timestamp = datetime.now().strftime('%y%m%d%H%M')
    base_name = os.path.basename(DPSPTH.temp_csv_path).replace('.csv', '')
    
    # Ensure the backup directory exists, if not, create it
    if not os.path.exists(DPSPTH.temp_csv_backup_dir):
        os.makedirs(DPSPTH.temp_csv_backup_dir)

    print(f"[green]backup existing csv into {DPSPTH.temp_csv_backup_dir}")

    backup_name = os.path.join(DPSPTH.temp_csv_backup_dir, f"{base_name}_backup_{timestamp}.csv")
    shutil.copy(DPSPTH.temp_csv_path, backup_name)

with open(new_file, 'w', encoding='utf-8') as target_file:
    target_file.write(content)

toc()
