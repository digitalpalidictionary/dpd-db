import os
import zipfile
from pathlib import Path

def zip_up_file(input_file: Path, output_file: Path, compression_level: int = 9, delete_original: bool = False):
    """
    Zip up an output file with compression and optionally delete the original file.
    
    Parameters:
    input_file (pathlib.Path): Path to the input file
    output_file (pathlib.Path): Path to the output file
    compression_level (int, optional): Compression level for the zip file, from 0 (no compression) to 9 (best compression). Defaults to 9.
    delete_original (bool, optional): Whether to delete the original file after zipping. Defaults to False.
    
    Raises:
    FileNotFoundError: If the input file does not exist
    PermissionError: If the user does not have permission to delete the file
    """
    # Check if the input file exists
    if not input_file.exists():
        raise FileNotFoundError(f"Input file {input_file} does not exist.")
    
    # Create the output directory if it doesn't exist
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Zip the output file with compression
    with zipfile.ZipFile(str(output_file), 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=compression_level) as zip_file:
        zip_file.write(str(input_file), os.path.basename(str(input_file)))
    
    # Optionally delete the original file
    if delete_original:
        try:
            input_file.unlink()
        except PermissionError:
            print(f"Unable to delete {input_file} due to permission error.")