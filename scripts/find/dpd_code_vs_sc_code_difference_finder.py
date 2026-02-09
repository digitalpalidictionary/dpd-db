#!/usr/bin/env python3

"""Find codes with different numeric parts between dpd_code and sc_code in SuttaInfo and write to TSV file."""

import re
from db.db_helpers import get_db_session
from db.models import SuttaInfo
from tools.paths import ProjectPaths
from tools.tsv_read_write import write_tsv_list


def extract_numeric_part(code: str) -> str:
    """Extract numeric part from a code (e.g., 'SN12.83-92' -> '12.83-92', 'KP1' -> '1')"""
    numeric_match = re.search(r"\d.*", code)
    return numeric_match.group() if numeric_match else ""


def extract_letter_prefix(code: str) -> str:
    """Extract letter prefix from a code (e.g., 'SN12.83-92' -> 'SN', 'KP1' -> 'KP')"""
    prefix_match = re.search(r"^[a-zA-Z]+", code)
    return prefix_match.group() if prefix_match else ""


def main():
    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)
    db = db_session.query(SuttaInfo).all()
    different_numeric_codes: list[list[str]] = []
    
    for i in db:
        if i.dpd_code and i.sc_code:
            dpd_prefix = extract_letter_prefix(i.dpd_code)
            sc_prefix = extract_letter_prefix(i.sc_code)
            
            # Only compare if prefixes are the same
            if dpd_prefix == sc_prefix and dpd_prefix:
                dpd_numeric = extract_numeric_part(i.dpd_code)
                sc_numeric = extract_numeric_part(i.sc_code)
                
                if dpd_numeric != sc_numeric:
                    different_numeric_codes.append([i.dpd_code, i.sc_code])
    
    # Write to TSV file in temp directory
    output_path = pth.temp_dir / "different_numeric_codes.tsv"
    write_tsv_list(
        file_path=str(output_path),
        header=["dpd_code", "sc_code"],
        data=different_numeric_codes
    )
    
    print(f"Found {len(different_numeric_codes)} codes with different numeric parts (same prefix)")
    print(f"TSV file created at: {output_path}")


if __name__ == "__main__":
    main()
