
"""
Allows natural sorting of lists of complex alpha-numeric names.
This is useful for sorting files with names like:
    'file-1.1.json', 'file-1.2.json', 'file-2.1.json', 'file-10.1.json'
    'file-10.2.json', 'file-11.1.json', 'file-11.2.json'
"""

import re
from pathlib import Path
from typing import Any


def alpha_num_key(filename: Any) -> tuple:
    pattern = re.compile(r'^([\-a-zA-Z]+)(\d+)(?:\.(\d+))?(.*)$')
    
    name_to_match = None
    if isinstance(filename, Path):
        name_to_match = filename.name
    elif isinstance(filename, str):
        name_to_match = filename

    if name_to_match:
        match = pattern.match(name_to_match)
        if match:
            prefix, num1_str, num2_str, suffix = match.groups()
            num1_int = int(num1_str)
            num2_int = int(num2_str) if num2_str is not None else -1
            return (0, prefix, num1_int, num2_int, suffix)

    return (1, str(filename), 0, 0, '')

def natural_sort(file_list: list[Any]) -> list[Any]:
    """
    Sort a list of alpha-numerical names into a natural order.
    
    Usage: 
        `sorted_files = natural_sort(file_list)`
    """

    if not isinstance(file_list, list):
        return []
    return sorted(file_list, key=alpha_num_key)

if __name__ == '__main__':

    target_dir = Path("resources/sc-data/sc_bilara_data/root/pli")
    files_to_sort = list(target_dir.glob('**/*.json'))

    sorted_files = natural_sort(files_to_sort)

    for i in sorted_files:
        if i.name.startswith("s"):
            print(i.name)
