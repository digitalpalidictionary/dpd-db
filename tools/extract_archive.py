#!/usr/bin/env python3

# unpack tar

import tarfile
import os
import sys

from tools.configger import config_test

def extract_archive(input_archive, output_directory):
    # Ensure the output directory exists or create it
    os.makedirs(output_directory, exist_ok=True)
    
    # Open the tar.gz file and extract all contents
    try:
        with tarfile.open(input_archive, 'r:gz') as archive:
            archive.extractall(path=output_directory)
        print(f"Successfully extracted to {output_directory}")
    except Exception as e:
        print(f"An error occurred: {e}")


def main():
    # Ensure that both input_archive and output_directory are provided
    if len(sys.argv) != 3:
        print("Usage: python extract_archive.py <input_archive> <output_directory>")
        sys.exit(1)
    
    input_archive = sys.argv[1]
    output_directory = sys.argv[2]
    
    extract_archive(input_archive, output_directory)

    
if __name__ == "__main__":
    if config_test("deconstructor", "include_cloud", "yes"):
        main()
    else:
        print("include_cloud is disabled")