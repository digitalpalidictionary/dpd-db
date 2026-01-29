#!/usr/bin/env python3

import sqlite3
import json
import re
from pathlib import Path
from natsort import natsorted
from tools.paths import ProjectPaths

def extract_tpr_codes() -> None:
    pth = ProjectPaths()
    db_path = Path.home() / ".local/share/tipitaka_pali_reader/tipitaka_pali.db"
    if not db_path.exists():
        print(f"Error: TPR database not found at {db_path}")
        return

    output_file = pth.tpr_codes_json_path

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Query unique sutta_shortcut from sutta_page_shortcut
    cursor.execute("SELECT DISTINCT sutta_shortcut FROM sutta_page_shortcut")
    codes = [row[0] for row in cursor.fetchall() if row[0]]
    
    conn.close()

    # Define Nikaya order
    nikaya_order = ["dn", "mn", "sn", "an", "kn"]
    
    def nikaya_sort_key(s: str) -> int:
        match = re.match(r"^([a-z]+)", s.lower())
        if match:
            prefix = match.group(1)
            try:
                return nikaya_order.index(prefix)
            except ValueError:
                return len(nikaya_order)
        return len(nikaya_order) + 1

    # Sort by nikaya order first, then naturally within each nikaya
    sorted_codes = natsorted(codes, key=lambda x: (nikaya_sort_key(x), x))

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(sorted_codes, f, ensure_ascii=False, indent=2)
    
    print(f"Successfully extracted {len(codes)} unique TPR codes to {output_file}")

if __name__ == "__main__":
    extract_tpr_codes()
