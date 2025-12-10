"""
Allows natural sorting of lists of complex alpha-numeric names.
This is useful for sorting files with names like:
    'file-1.1.json', 'file-1.2.json', 'file-2.1.json', 'file-10.1.json'
    'file-10.2.json', 'file-11.1.json', 'file-11.2.json'
    'an-3.json', 'an-3-2.json', 'an-3-3.json'
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


def alpha_num_key_hyphenated(filename: Any) -> tuple:
    """
    Specialized function to handle hyphen-separated numbering like 'an-3.json' and 'an-3-2.json'
    Split by hyphens to handle multiple numeric parts
    """
    name_to_match = None
    if isinstance(filename, Path):
        name_to_match = filename.name
    elif isinstance(filename, str):
        name_to_match = filename

    if name_to_match:
        # Remove extension first
        parts = name_to_match.replace('.json', '').replace('.txt', '').replace('.', '_').split('-')
        
        # The first two parts form the prefix, e.g. ['an', '3'] -> 'an-3-'
        if len(parts) >= 2:
            try:
                prefix = parts[0] + "-"
                num1_int = int(parts[1])
                
                # Second number exists if there are more than 2 parts
                num2_int = -1
                if len(parts) > 2:
                    num2_int = int(parts[2])
                
                # Get extension
                _, *_, ext = name_to_match.rpartition('.')
                suffix = '.' + ext if ext else ''
                
                return (0, prefix, num1_int, num2_int, suffix)
            except ValueError:
                # Handle cases where conversion to int fails
                pass

    # Fallback for filenames that don't match the expected pattern
    return (1, str(filename), 0, 0, '')


def natural_sort(file_list: list[Any]) -> list[Any]:
    """
    Sort a list of alpha-numerical names into a natural order (original pattern).
    Handles formats like: 'file-1.1.json', 'file-2.1.json'
    
    Usage: 
        `sorted_files = natural_sort(file_list)`
    """

    if not isinstance(file_list, list):
        return []
    return sorted(file_list, key=alpha_num_key)


def natural_sort_hyphenated(file_list: list[Any]) -> list[Any]:
    """
    Sort a list of alpha-numerical names into a natural order (hyphenated pattern).
    Handles formats like: 'an-3.json', 'an-3-2.json', 'an-3-3.json' where
    'an-3.json' should come before 'an-3-2.json'.
    
    Usage: 
        `sorted_files = natural_sort_hyphenated(file_list)`
    """

    if not isinstance(file_list, list):
        return []
    return sorted(file_list, key=alpha_num_key_hyphenated)


if __name__ == '__main__':

    target_dir = Path("resources/sc-data/sc_bilara_data/root/pli")
    files_to_sort = list(target_dir.glob('**/*.json'))

    sorted_files = natural_sort(files_to_sort)

    for i in sorted_files:
        if i.name.startswith("s"):
            print(i.name)